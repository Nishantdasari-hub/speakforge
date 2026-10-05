"""API/state/negative-case regression suite. SMTP and speech also run in live smoke tests."""
import io
import os
import tempfile
import unittest
import wave
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from urllib.parse import urlsplit

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import jwt

from app.main import app
from app.database import Base, get_db
from app import models, worker
from app.routes import auth, test as routes
from app.services import auth_service, ai_scoring
from app.utils.token import create_verification_token, SECRET_KEY


def wav_data(seconds=1):
    output=io.BytesIO()
    with wave.open(output,"wb") as value:
        value.setnchannels(1)
        value.setsampwidth(2)
        value.setframerate(16000)
        value.writeframes(b"\0\0"*int(seconds*16000))
    return output.getvalue()


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
        event.listen(self.engine,"connect",lambda conn,_: conn.execute("PRAGMA foreign_keys=ON"))
        Base.metadata.create_all(self.engine)
        self.Session=sessionmaker(bind=self.engine)
        def database():
            with self.Session() as session: yield session
        app.dependency_overrides[get_db]=database
        app.state.limiter.enabled=False
        self.temp=tempfile.TemporaryDirectory()
        self.patches=[patch.object(auth,"conf",object()),patch.object(auth,"send_verification_email",new_callable=AsyncMock),patch.object(auth,"send_reset_password_email",new_callable=AsyncMock),patch.object(routes,"UPLOAD_DIR",Path(self.temp.name)),patch.object(worker,"SessionLocal",self.Session),patch.dict(os.environ,{"ADMIN_SECRET_KEY":"test-admin-secret"})]
        self.mocks=[p.start() for p in self.patches]
        self.client=TestClient(app)
        self.admin=self.make_user("admin@example.com",True)
        self.user=self.make_user("learner@example.com")
        self.other=self.make_user("other@example.com")

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        app.state.limiter.enabled=True
        for p in reversed(self.patches): p.stop()
        self.engine.dispose()
        self.temp.cleanup()

    def make_user(self,email,admin=False):
        r=self.client.post('/auth/register',json={"email":email,"name":"Test User","password":"secure-pass-123","is_admin":admin,"admin_key":"test-admin-secret" if admin else None})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.client.get('/auth/verify-email',params={"token":create_verification_token(email)},follow_redirects=False).status_code,307)
        r=self.client.post('/auth/login',json={"email":email,"password":"secure-pass-123"})
        self.assertEqual(r.status_code,200,r.text)
        return {"Authorization":"Bearer "+r.json()['access_token']}

    def make_test(self,kind='text',questions=1):
        r=self.client.post('/tests/',headers=self.admin,json={"title":"Practice","description":"A test"})
        self.assertEqual(r.status_code,200,r.text)
        tid=r.json()['id']; ids=[]
        for n in range(questions):
            r=self.client.post(f'/tests/{tid}/questions',headers=self.admin,json={"question_text":f"Question {n+1}","question_type":kind,"time_limit":30,"order_number":n+1})
            self.assertEqual(r.status_code,200,r.text); ids.append(r.json()['id'])
        return tid,ids

    def start(self,tid,headers=None):
        r=self.client.post(f'/tests/{tid}/start',headers=headers or self.user)
        self.assertEqual(r.status_code,200,r.text)
        return r.json()['attempt_id']

    def answer(self,aid,qid,text='I enjoy learning English. I practice every day with my friends.',headers=None):
        return self.client.post(f'/tests/submit-answer/{qid}',headers=headers or self.user,data={"attempt_id":aid,"text_answer":text})

    def submit(self,tid,aid):
        return self.client.post(f'/tests/{tid}/submit',headers=self.user,params={"attempt_id":aid})

    def report(self,tid,aid,headers=None):
        return self.client.get(f'/tests/report/{tid}',headers=headers or self.user,params={"attempt_id":aid})

    def finish_jobs(self,score=8):
        result={"grammar_score":score,"fluency_score":score,"final_score":score,"grammar_errors":0,"word_count":20,"feedback":"Fixture feedback"}
        with patch.object(worker,'evaluate_answer',return_value=result):
            while job:=worker.claim_job(): worker.run_job(job)

    def test_registration_validation_normalization_and_mail_failure(self):
        invalid=[{"email":"bad"},{"password":"short"},{"password":"é"*40},{"name":" "}]
        for item in invalid:
            body={"email":"new@example.com","password":"secure-pass-123","name":"Valid",**item}
            self.assertEqual(self.client.post('/auth/register',json=body).status_code,422)
        self.assertEqual(self.client.post('/auth/register',json={"email":"LEARNER@example.com","password":"secure-pass-123","name":"Valid"}).status_code,400)
        self.mocks[1].side_effect=RuntimeError('SMTP offline')
        self.assertEqual(self.client.post('/auth/register',json={"email":"new@example.com","password":"secure-pass-123","name":"Valid"}).status_code,503)
        with self.Session() as db: self.assertIsNone(db.query(models.User).filter_by(email='new@example.com').first())
        with patch.object(auth,'conf',None):
            self.assertEqual(self.client.post('/auth/register',json={"email":"new@example.com","password":"secure-pass-123","name":"Valid"}).status_code,503)

    def test_unverified_login_and_resend(self):
        body={"email":"unverified@example.com","password":"secure-pass-123","name":"Valid"}
        self.assertEqual(self.client.post('/auth/register',json=body).status_code,200)
        self.assertEqual(self.client.post('/auth/login',json=body).status_code,403)
        self.assertEqual(self.client.post('/auth/resend-verification',json={"email":body['email']}).status_code,200)
        self.mocks[1].assert_awaited()
        self.assertEqual(self.client.post('/auth/resend-verification',json={"email":"missing@example.com"}).status_code,200)
        self.assertEqual(self.client.get('/auth/verify-email',params={'token':'bad'}).status_code,400)

    def test_password_reset_is_single_use_and_revokes_access(self):
        self.assertEqual(self.client.post('/auth/forgot-password',json={'email':'learner@example.com'}).status_code,200)
        token=self.mocks[2].call_args.args[1].rsplit('/',1)[1]
        with self.Session() as db:
            user=db.query(models.User).filter_by(email='learner@example.com').one()
            self.assertNotEqual(user.reset_token,token)
        data={'token':token,'new_password':'new-secure-pass'}
        self.assertEqual(self.client.post('/auth/reset-password',json=data).status_code,200)
        self.assertEqual(self.client.post('/auth/reset-password',json=data).status_code,400)
        self.assertEqual(self.client.get('/tests/me/results',headers=self.user).status_code,401)
        self.assertEqual(self.client.post('/auth/login',json={'email':'learner@example.com','password':'secure-pass-123'}).status_code,400)
        self.assertEqual(self.client.post('/auth/login',json={'email':'learner@example.com','password':'new-secure-pass'}).status_code,200)

    def test_expired_reset_and_mail_rollback(self):
        self.client.post('/auth/forgot-password',json={'email':'learner@example.com'})
        token=self.mocks[2].call_args.args[1].rsplit('/',1)[1]
        with self.Session() as db:
            user=db.query(models.User).filter_by(email='learner@example.com').one()
            user.reset_token_expiry=datetime.utcnow()-timedelta(seconds=1);db.commit()
        self.assertEqual(self.client.post('/auth/reset-password',json={'token':token,'new_password':'secure-pass-456'}).status_code,400)
        self.mocks[2].side_effect=RuntimeError('SMTP failed')
        self.assertEqual(self.client.post('/auth/forgot-password',json={'email':'learner@example.com'}).status_code,503)
        with self.Session() as db:
            self.assertEqual(db.query(models.User).filter_by(email='learner@example.com').one().reset_token,auth_service.digest_token(token))
        self.assertEqual(self.client.post('/auth/forgot-password',json={'email':'missing@example.com'}).status_code,200)

    def test_auth_role_and_token_purpose_guards(self):
        for path in ['/tests/me/results','/tests/me/dashboard','/tests/me/answers','/tests/admin/analytics']:
            self.assertEqual(self.client.get(path).status_code,401)
        self.assertEqual(self.client.get('/tests/admin/analytics',headers=self.user).status_code,403)
        self.assertEqual(self.client.post('/tests/',headers=self.user,json={'title':'No','description':''}).status_code,403)
        verify=create_verification_token('learner@example.com')
        self.assertEqual(self.client.get('/tests/me/results',headers={'Authorization':'Bearer '+verify}).status_code,401)
        access=self.user['Authorization'].split()[1]
        self.assertEqual(self.client.get('/auth/verify-email',params={'token':access}).status_code,400)
        expired=jwt.encode({'sub':'learner@example.com','purpose':'access','version':0,'exp':datetime.utcnow()-timedelta(seconds=1)},SECRET_KEY,algorithm='HS256')
        self.assertEqual(self.client.get('/tests/me/results',headers={'Authorization':'Bearer '+expired}).status_code,401)

    def test_admin_crud_and_schema_constraints(self):
        tid,ids=self.make_test(questions=2)
        self.assertEqual(self.client.put(f'/tests/{tid}',headers=self.admin,json={'title':'Edited','description':'Changed'}).status_code,200)
        q={'question_text':'Edited question','question_type':'audio','time_limit':10,'order_number':3}
        self.assertEqual(self.client.put(f'/tests/{tid}/questions/{ids[0]}',headers=self.admin,json=q).status_code,200)
        self.assertEqual(self.client.get(f'/tests/{tid}/questions',headers=self.user).json()[0]['id'],ids[1])
        for values in [{'question_type':'invalid'},{'time_limit':0},{'question_text':' '},{'order_number':-1}]:
            self.assertEqual(self.client.post(f'/tests/{tid}/questions',headers=self.admin,json={**q,**values}).status_code,422)
        self.assertEqual(self.client.delete(f'/tests/{tid}/questions/{ids[0]}',headers=self.admin).status_code,200)
        self.assertEqual(self.client.delete(f'/tests/{tid}',headers=self.admin).status_code,200)
        self.assertEqual(self.client.get(f'/tests/{tid}').status_code,404)
        self.assertEqual(self.client.get('/tests/999999/questions',headers=self.user).status_code,404)

    def test_attempt_submission_idempotence_retakes_and_consistent_results(self):
        tid,ids=self.make_test(questions=2);aid=self.start(tid)
        self.assertEqual(self.start(tid),aid)
        self.assertEqual(self.submit(tid,aid).status_code,409)
        self.assertEqual(self.answer(aid,ids[0]).status_code,200)
        self.assertEqual(self.answer(aid,ids[0],text='Updated answer.').status_code,200)
        with self.Session() as db: self.assertEqual(db.query(models.QuestionAnswer).count(),1)
        self.assertEqual(self.answer(aid,ids[1]).status_code,200)
        self.assertEqual(self.submit(tid,aid).status_code,200)
        self.assertEqual(self.submit(tid,aid).status_code,200)
        self.assertEqual(self.answer(aid,ids[0]).status_code,409)
        self.assertEqual(self.report(tid,aid).json()['status'],'processing')
        self.finish_jobs(8)
        result=self.report(tid,aid).json();self.assertEqual(result['overall_score'],8)
        stats=self.client.get('/tests/me/dashboard',headers=self.user).json()
        self.assertEqual(stats['tests_completed'],1);self.assertEqual(stats['average_score'],8)
        self.assertEqual(self.client.get('/tests/me/results',headers=self.user).json()[0]['score'],8)
        second=self.start(tid);self.assertNotEqual(second,aid)
        for qid in ids: self.answer(second,qid)
        self.submit(tid,second);self.finish_jobs(4)
        self.assertEqual(self.report(tid,aid).json()['overall_score'],8)
        self.assertEqual(self.client.get('/tests/me/dashboard',headers=self.user).json()['average_score'],6)
        self.assertEqual(self.client.get('/tests/admin/analytics',headers=self.admin).json()['total_attempts'],2)

    def test_ownership_and_used_content_protection(self):
        tid,ids=self.make_test();aid=self.start(tid)
        self.assertEqual(self.answer(aid,ids[0],headers=self.other).status_code,404)
        self.assertEqual(self.report(tid,aid,headers=self.other).status_code,404)
        self.assertEqual(self.client.post(f'/tests/attempts/{aid}/retry',headers=self.other).status_code,404)
        self.assertEqual(self.client.delete(f'/tests/{tid}',headers=self.admin).status_code,409)
        self.assertEqual(self.client.delete(f'/tests/{tid}/questions/{ids[0]}',headers=self.admin).status_code,409)
        other,others=self.make_test()
        self.assertEqual(self.answer(aid,others[0]).status_code,404)
        self.assertEqual(self.client.get('/tests/report/9999',headers=self.user).status_code,404)

    def test_empty_tests_answers_and_upload_validation(self):
        r=self.client.post('/tests/',headers=self.admin,json={'title':'Empty','description':''});tid=r.json()['id']
        self.assertEqual(self.client.post(f'/tests/{tid}/start',headers=self.user).status_code,400)
        tid,ids=self.make_test();aid=self.start(tid)
        for value in ['',' ','x'*10001]: self.assertEqual(self.answer(aid,ids[0],value).status_code,422)
        tid,ids=self.make_test('audio');aid=self.start(tid)
        self.assertEqual(self.answer(aid,ids[0]).status_code,422)
        for content,status in [(b'corrupt',422),(b'x'*(10*1024*1024+1),413),(wav_data(.1),422)]:
            r=self.client.post(f'/tests/submit-answer/{ids[0]}',headers=self.user,data={'attempt_id':aid},files={'audio':('clip.wav',content,'audio/wav')})
            self.assertEqual(r.status_code,status,r.text)
        self.assertEqual(list(Path(self.temp.name).iterdir()),[])
        r=self.client.post(f'/tests/submit-answer/{ids[0]}',headers=self.user,data={'attempt_id':aid},files={'audio':('clip.wav',wav_data(),'audio/wav')})
        self.assertEqual(r.status_code,200,r.text)
        self.submit(tid,aid)
        with patch.object(worker,'transcribe_audio',return_value=('',1)):
            worker.run_job(worker.claim_job())
        report=self.report(tid,aid).json()
        self.assertEqual(report['status'],'completed');self.assertEqual(report['overall_score'],0)
        self.assertEqual(report['answers'][0]['feedback'],'No speech detected.')

    def test_worker_failure_retry_stale_lease_and_fencing(self):
        tid,ids=self.make_test();aid=self.start(tid);self.answer(aid,ids[0]);self.submit(tid,aid)
        first=worker.claim_job();self.assertIsNone(worker.claim_job())
        with self.Session() as db:
            answer=db.get(models.QuestionAnswer,first['id']);answer.score_started_at=datetime.utcnow()-timedelta(seconds=601);db.commit()
        next_job=worker.claim_job();self.assertNotEqual(first['token'],next_job['token'])
        with patch.object(worker,'evaluate_answer',side_effect=RuntimeError('offline')):
            worker.run_job(first)  # stale worker cannot update the new lease
            with self.Session() as db: self.assertEqual(db.get(models.QuestionAnswer,first['id']).score_status,'processing')
            worker.run_job(next_job)
            worker.run_job(worker.claim_job())
        self.assertEqual(self.report(tid,aid).json()['status'],'failed')
        self.assertEqual(self.client.post(f'/tests/attempts/{aid}/retry',headers=self.user).status_code,200)
        self.finish_jobs();self.assertEqual(self.report(tid,aid).json()['status'],'completed')

    def test_login_rate_limit(self):
        app.state.limiter.reset();app.state.limiter.enabled=True
        codes=[self.client.post('/auth/login',json={'email':'missing@example.com','password':'bad'}).status_code for _ in range(11)]
        self.assertEqual(codes[-1],429)
        app.state.limiter.reset()


class ScoringTests(unittest.TestCase):
    def test_grammar_quality_and_short_answer_cap(self):
        tool=Mock()
        with patch.object(ai_scoring,'get_language_tool',return_value=tool):
            text='I enjoy learning new languages. I practice with my friends every day because speaking regularly helps me communicate clearly and confidently.'
            tool.check.return_value=[]
            good=ai_scoring.evaluate_answer('Introduce yourself',text,answer_type='text')
            tool.check.return_value=[SimpleNamespace(offset=0,error_length=1,message='Fixture issue',replacements=[]) for _ in range(10)]
            bad=ai_scoring.evaluate_answer('Introduce yourself',text,answer_type='text')
            self.assertGreater(good['final_score'],bad['final_score'])
            self.assertEqual(bad['grammar_errors'],10)
            tool.check.return_value=[]
            self.assertLessEqual(ai_scoring.evaluate_answer('', 'Hello', answer_type='text')['final_score'],3)
        self.assertEqual(ai_scoring.evaluate_answer('','...')['final_score'],0)

    def test_grammar_errors_are_not_hidden_by_integer_rounding(self):
        tool=Mock()
        with patch.object(ai_scoring,'get_language_tool',return_value=tool):
            tool.check.return_value=[]
            good=ai_scoring.evaluate_answer('', 'I enjoy learning English with my friends. We practice every morning because regular conversations help us communicate clearly and confidently in different situations.', answer_type='text')
            tool.check.return_value=[SimpleNamespace(offset=0,error_length=1,message='Fixture issue',replacements=[]) for _ in range(6)]
            bad=ai_scoring.evaluate_answer('', 'He go to school yesterday. She have many book and they was very happy. I is learning English because my friend do not knows the answers.', answer_type='text')
            self.assertGreater(good['final_score'],bad['final_score'])
            self.assertLessEqual(bad['grammar_score'],6)

    def test_audio_decode_duration_silence_and_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sound.wav';path.write_bytes(wav_data(2))
            self.assertEqual(ai_scoring.get_audio_duration(path),2)
            self.assertTrue(ai_scoring.is_silent(path))
            self.assertEqual(ai_scoring.transcribe_audio(path),('',2))
            with self.assertRaises(ValueError): ai_scoring.decode_audio_file(path,max_seconds=1)
            path.write_bytes(b'bad')
            with self.assertRaises(ValueError): ai_scoring.decode_audio_file(path)

    def test_pace_and_score_bounds(self):
        self.assertGreater(ai_scoring.calculate_speaking_fluency('',30,15),ai_scoring.calculate_speaking_fluency('',30,120))
        self.assertEqual(ai_scoring.calculate_speaking_fluency('',10,0),0)
        for count in [0,1,10,100,10000]:
            self.assertTrue(0 <= ai_scoring.calculate_writing_fluency('Sentence. Next.',count) <= 10)
            self.assertTrue(0 <= ai_scoring.calculate_speaking_fluency('',count,30) <= 10)
