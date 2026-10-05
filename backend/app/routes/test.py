from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import get_current_admin, get_current_user
from app.services.ai_scoring import decode_audio_file
from app.services.attempts import get_attempt, summarize
from app.config import UPLOAD_DIR
from app import models, schemas

router = APIRouter(prefix="/tests", tags=["Tests"])
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def get_test_or_404(db, test_id, lock=False):
    query = db.query(models.Test).filter_by(id=test_id)
    if lock:
        query = query.with_for_update()
    test = query.first()
    if not test:
        raise HTTPException(404, "Test not found")
    return test


def require_unused(db, test_id):
    # Published assessment content must remain stable for reports and active users.
    if db.query(models.Attempt.id).filter_by(test_id=test_id).first() or db.query(models.Result.id).filter_by(test_id=test_id).first():
        raise HTTPException(409, "This test has attempts. Create a new test to change its content.")


@router.get("/", response_model=list[schemas.TestResponse])
def get_tests(db: Session = Depends(get_db)):
    return db.query(models.Test).order_by(models.Test.id).all()


@router.post("/", response_model=schemas.TestResponse)
def create_test(test: schemas.TestCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    value = models.Test(**test.model_dump())
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@router.get("/{test_id:int}", response_model=schemas.TestResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):
    return get_test_or_404(db, test_id)


@router.put("/{test_id:int}", response_model=schemas.TestResponse)
def update_test(test_id: int, test: schemas.TestCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    value = get_test_or_404(db, test_id, lock=True)
    require_unused(db, test_id)
    for key, item in test.model_dump().items():
        setattr(value, key, item)
    db.commit()
    db.refresh(value)
    return value


@router.delete("/{test_id:int}")
def delete_test(test_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    value = get_test_or_404(db, test_id, lock=True)
    require_unused(db, test_id)
    for question in list(value.questions):
        db.delete(question)
    db.flush()
    db.delete(value)
    db.commit()
    return {"message":"Test deleted successfully"}


@router.post("/{test_id:int}/questions", response_model=schemas.QuestionResponse)
def add_question(test_id: int, question: schemas.QuestionCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    get_test_or_404(db, test_id, lock=True)
    require_unused(db, test_id)
    if db.query(models.Question).filter_by(test_id=test_id).count() >= 50:
        raise HTTPException(400, "A test may contain at most 50 questions")
    value = models.Question(test_id=test_id, **question.model_dump())
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@router.get("/{test_id:int}/questions", response_model=list[schemas.QuestionResponse])
def get_questions(test_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    get_test_or_404(db, test_id)
    return db.query(models.Question).filter_by(test_id=test_id).order_by(models.Question.order_number, models.Question.id).all()


@router.put("/{test_id:int}/questions/{question_id}", response_model=schemas.QuestionResponse)
def update_question(test_id: int, question_id: int, question: schemas.QuestionCreate, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    get_test_or_404(db, test_id, lock=True)
    require_unused(db, test_id)
    value = db.query(models.Question).filter_by(id=question_id, test_id=test_id).first()
    if not value:
        raise HTTPException(404, "Question not found")
    for key, item in question.model_dump().items():
        setattr(value, key, item)
    db.commit()
    db.refresh(value)
    return value


@router.delete("/{test_id:int}/questions/{question_id}")
def delete_question(test_id: int, question_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    get_test_or_404(db, test_id, lock=True)
    require_unused(db, test_id)
    value = db.query(models.Question).filter_by(id=question_id, test_id=test_id).first()
    if not value:
        raise HTTPException(404, "Question not found")
    db.delete(value)
    db.commit()
    return {"message":"Question deleted successfully"}


@router.post("/{test_id:int}/start")
def start_test(test_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    test = get_test_or_404(db, test_id, lock=True)
    if not test.questions:
        raise HTTPException(400, "This test has no questions yet")
    attempt = db.query(models.Attempt).filter_by(user_id=user.id, test_id=test_id, submitted_at=None).first()
    if not attempt:
        attempt = models.Attempt(user_id=user.id, test_id=test_id)
        db.add(attempt)
        db.flush()
    db.commit()
    return {"attempt_id":attempt.id,"answered_question_ids":[a.question_id for a in attempt.answers]}


@router.post("/submit-answer/{question_id}")
def submit_answer(question_id: int, attempt_id: int = Form(...), audio: UploadFile = File(None), text_answer: str = Form(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    attempt = get_attempt(db, attempt_id, user.id, lock=True)
    if attempt.submitted_at:
        raise HTTPException(409, "This attempt is already submitted")
    question = db.query(models.Question).filter_by(id=question_id, test_id=attempt.test_id).first()
    if not question:
        raise HTTPException(404, "Question not found in this attempt")
    if audio and text_answer is not None:
        raise HTTPException(422, "Send one answer type")
    path = None
    if question.question_type == "audio":
        if not audio:
            raise HTTPException(422, "An audio recording is required")
        path = UPLOAD_DIR / f"{uuid4().hex}.audio"
        try:
            size = 0
            with path.open("wb") as target:
                while chunk := audio.file.read(64 * 1024):
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, "Audio must be at most 10 MB")
                    target.write(chunk)
            decode_audio_file(path, max_seconds=min(300, question.time_limit + 5))
        except ValueError as exc:
            path.unlink(missing_ok=True)
            raise HTTPException(422, str(exc)) from exc
        except Exception:
            path.unlink(missing_ok=True)
            raise
        finally:
            audio.file.close()
    elif audio or not text_answer or not text_answer.strip() or len(text_answer) > 10000:
        raise HTTPException(422, "Provide a text answer of 1–10000 characters")
    answer = db.query(models.QuestionAnswer).filter_by(attempt_id=attempt.id, question_id=question.id).first()
    old_path = answer.audio_path if answer else None
    if not answer:
        answer = models.QuestionAnswer(attempt_id=attempt.id, user_id=user.id, question_id=question.id)
        db.add(answer)
    answer.audio_path = str(path) if path else None
    answer.written_answer = text_answer.strip() if text_answer else None
    try:
        db.commit()
    except Exception:
        if path:
            path.unlink(missing_ok=True)
        raise
    if old_path:
        Path(old_path).unlink(missing_ok=True)
    return {"message":"Answer saved", "answer_id":answer.id}


@router.post("/{test_id:int}/submit")
def submit_test(test_id: int, attempt_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    attempt = get_attempt(db, attempt_id, user.id, lock=True)
    if attempt.test_id != test_id:
        raise HTTPException(404, "Attempt not found")
    if not attempt.submitted_at:
        expected = db.query(models.Question).filter_by(test_id=test_id).count()
        if not expected or len(attempt.answers) != expected:
            raise HTTPException(409, "Answer every question before submitting")
        attempt.submitted_at = datetime.utcnow()
        for answer in attempt.answers:
            answer.score_status = "queued"
        db.commit()
    return {"message":"Test submitted", "attempt_id":attempt.id, "status":summarize(attempt)["status"]}


@router.post("/attempts/{attempt_id}/retry")
def retry_scoring(attempt_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    attempt = get_attempt(db, attempt_id, user.id, lock=True)
    for answer in attempt.answers:
        if answer.score_status == "failed":
            answer.score_status, answer.score_error, answer.score_attempts = "queued", None, 0
    db.commit()
    return {"status":summarize(attempt)["status"]}


@router.get("/me/results")
def get_user_results(db: Session = Depends(get_db), user=Depends(get_current_user)):
    attempts = db.query(models.Attempt).filter(models.Attempt.user_id == user.id, models.Attempt.submitted_at.isnot(None)).order_by(models.Attempt.id.desc()).all()
    return [summarize(attempt) for attempt in attempts]


@router.get("/me/dashboard")
def get_dashboard(db: Session = Depends(get_db), user=Depends(get_current_user)):
    results = get_user_results(db, user)
    completed = [result for result in results if result["status"] == "completed"]
    avg = round(sum(r["score"] for r in completed) / len(completed), 1) if completed else 0
    return {"tests_completed":len(completed), "average_score":avg,
            "level":"Advanced practice" if avg >= 8 else "Developing practice"}


@router.get("/me/answers")
def get_recent_answers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    answers = db.query(models.QuestionAnswer).filter_by(user_id=user.id, score_status="completed").order_by(models.QuestionAnswer.id.desc()).limit(10).all()
    return [{"id":a.id,"question_id":a.question_id,"question_text":a.question.question_text,
             "final_score":a.final_score,"word_count":a.word_count,"created_at":a.created_at.isoformat()} for a in answers]


@router.get("/admin/analytics")
def analytics(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return {"total_tests":db.query(models.Test).count(),"total_questions":db.query(models.Question).count(),
            "total_users":db.query(models.User).count(),
            "total_attempts":db.query(models.Attempt).filter(models.Attempt.submitted_at.isnot(None)).count()}
