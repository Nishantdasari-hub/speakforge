from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import os
import shutil
from datetime import datetime

from ..database import SessionLocal
from ..services.auth_service import get_current_admin, get_current_user
from .. import models, schemas
from app.services.ai_scoring import transcribe_audio, evaluate_answer

router = APIRouter(
    prefix="/tests",
    tags=["Tests"]
)

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


# ================= DATABASE =================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ======================================================
# GET ALL TESTS
# ======================================================

@router.get("/", response_model=List[schemas.TestResponse])
def get_tests(db: Session = Depends(get_db)):
    return db.query(models.Test).all()


# ======================================================
# CREATE TEST (ADMIN)
# ======================================================

@router.post("/", response_model=schemas.TestResponse)
def create_test(
    test: schemas.TestCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):

    new_test = models.Test(
        title=test.title,
        description=test.description
    )

    db.add(new_test)
    db.commit()
    db.refresh(new_test)

    return new_test


# ======================================================
# GET SINGLE TEST
# ======================================================

@router.get("/{test_id}", response_model=schemas.TestResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):

    test = db.query(models.Test).filter(models.Test.id == test_id).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    return test


# ======================================================
# UPDATE TEST (ADMIN)
# ======================================================

@router.put("/{test_id}", response_model=schemas.TestResponse)
def update_test(
    test_id: int,
    test: schemas.TestCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):

    existing = db.query(models.Test).filter(models.Test.id == test_id).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Test not found")

    existing.title = test.title
    existing.description = test.description

    db.commit()
    db.refresh(existing)

    return existing


# ======================================================
# ADD QUESTION (ADMIN)
# ======================================================

@router.post("/{test_id}/questions", response_model=schemas.QuestionResponse)
def add_question(
    test_id: int,
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):

    test = db.query(models.Test).filter(models.Test.id == test_id).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    new_question = models.Question(
        question_text=question.question_text,
        question_type=question.question_type,
        time_limit=question.time_limit,
        order_number=question.order_number,
        test_id=test_id
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return new_question


# ======================================================
# GET QUESTIONS
# ======================================================

@router.get("/{test_id}/questions")
def get_questions(
    test_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    questions = db.query(models.Question).filter(
        models.Question.test_id == test_id
    ).all()

    return questions


# ======================================================
# UPDATE QUESTION (ADMIN)
# ======================================================

@router.put("/{test_id}/questions/{question_id}", response_model=schemas.QuestionResponse)
def update_question(
    test_id: int,
    question_id: int,
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):

    existing = db.query(models.Question).filter(
        models.Question.id == question_id,
        models.Question.test_id == test_id
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Question not found")

    existing.question_text = question.question_text
    existing.question_type = question.question_type
    existing.time_limit = question.time_limit
    existing.order_number = question.order_number

    db.commit()
    db.refresh(existing)

    return existing


# ======================================================
# DELETE QUESTION (ADMIN)
# ======================================================

@router.delete("/{test_id}/questions/{question_id}")
def delete_question(
    test_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):

    question = db.query(models.Question).filter(
        models.Question.id == question_id,
        models.Question.test_id == test_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.query(models.QuestionAnswer).filter(
        models.QuestionAnswer.question_id == question_id
    ).delete()

    db.delete(question)
    db.commit()

    return {"message": "Question deleted successfully"}


# ======================================================
# SUBMIT AUDIO ANSWER
# ======================================================
MAX_FILE_SIZE = 5 * 1024 * 1024
@router.post("/submit-answer/{question_id}")
async def submit_answer(
    question_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):

    # -------- FILE TYPE VALIDATION --------
    if file.content_type not in ["audio/webm", "audio/wav"]:
        raise HTTPException(status_code=400, detail="Invalid audio format")

    # -------- FILE SIZE VALIDATION --------
    contents = await file.read()

    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    # Reset file pointer after reading
    file.file.seek(0)

    filename = f"{datetime.now().timestamp()}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text_answer, audio_duration = transcribe_audio(filepath)

    question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    evaluation = evaluate_answer(
        question.question_text,
        text_answer,
        audio_duration
    )

    answer = models.QuestionAnswer(
        user_id=user.id,
        question_id=question_id,
        audio_path=filepath,
        transcribed_text=text_answer,
        grammar_score=evaluation.get("grammar_score"),
        fluency_score=evaluation.get("fluency_score"),
        final_score=evaluation.get("final_score"),
        word_count=evaluation.get("word_count"),
        feedback=evaluation.get("feedback")
    )

    db.add(answer)
    db.commit()

    return {
        "message": "Answer processed",
        "final_score": evaluation.get("final_score"),
        "grammar_score": evaluation.get("grammar_score"),
        "fluency_score": evaluation.get("fluency_score"),
        "feedback": evaluation.get("feedback")
    }


# ======================================================
# SUBMIT TEXT ANSWER
# ======================================================

@router.post("/submit-text-answer/{question_id}")
def submit_text_answer(
    question_id: int,
    data: schemas.TextAnswer,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    evaluation = evaluate_answer(
        question.question_text,
        data.answer,
        None,
        answer_type="text"
    )

    answer = models.QuestionAnswer(
        user_id=current_user.id,
        question_id=question_id,
        written_answer=data.answer,
        final_score=evaluation.get("final_score"),
        grammar_score=evaluation.get("grammar_score"),
        fluency_score=evaluation.get("fluency_score"),
        word_count=evaluation.get("word_count"),
        feedback=evaluation.get("feedback")
    )

    db.add(answer)
    db.commit()

    return {
        "message": "Text answer submitted",
        "score": evaluation.get("final_score")
    }


# ======================================================
# USER DASHBOARD
# ======================================================

@router.get("/me/dashboard")
def get_user_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    answers = db.query(models.QuestionAnswer).filter(
        models.QuestionAnswer.user_id == current_user.id
    ).all()

    if not answers:
        return {
            "tests_completed": 0,
            "average_score": 0,
            "level": "Beginner"
        }

    total = len(answers)

    avg = round(
        sum(a.final_score or 0 for a in answers) / total,
        1
    )

    if avg >= 9:
        level = "Expert"
    elif avg >= 8:
        level = "Advanced"
    elif avg >= 7:
        level = "Upper-Intermediate"
    elif avg >= 6:
        level = "Intermediate"
    else:
        level = "Beginner"

    return {
        "tests_completed": total,
        "average_score": avg,
        "level": level
    }


# ======================================================
# USER RECENT ANSWERS
# ======================================================

# ======================================================
# GET USER RECENT ANSWERS
# ======================================================

@router.get("/me/answers")
def get_user_recent_answers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get user's recent answers"""

    answers = db.query(models.QuestionAnswer).filter(
        models.QuestionAnswer.user_id == current_user.id
    ).order_by(models.QuestionAnswer.id.desc()).limit(10).all()

    result = []

    for answer in answers:
        result.append({
            "id": answer.id,
            "question_id": answer.question_id if answer.question_id else 0,
            "final_score": answer.final_score if answer.final_score else 0,
            "word_count": answer.word_count if answer.word_count else 0,
            "created_at": answer.created_at.isoformat() if hasattr(answer, "created_at") and answer.created_at else None
        })

    return result
# ======================================================
# ADMIN ANALYTICS
# ======================================================

@router.get("/admin/analytics")
def get_admin_analytics(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):

    total_users = db.query(models.User).count()
    total_tests = db.query(models.Test).count()
    total_questions = db.query(models.Question).count()
    total_attempts = db.query(models.QuestionAnswer).count()

    return {
        "total_users": total_users,
        "total_tests": total_tests,
        "total_questions": total_questions,
        "total_attempts": total_attempts
    }


# ======================================================
# DELETE TEST
# ======================================================

@router.delete("/{test_id}")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):

    test = db.query(models.Test).filter(
        models.Test.id == test_id
    ).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    question_ids = [
        q.id for q in db.query(models.Question).filter(
            models.Question.test_id == test_id
        ).all()
    ]

    if question_ids:
        db.query(models.QuestionAnswer).filter(
            models.QuestionAnswer.question_id.in_(question_ids)
        ).delete(synchronize_session=False)

        db.query(models.Question).filter(
            models.Question.test_id == test_id
        ).delete(synchronize_session=False)

    db.query(models.Result).filter(
        models.Result.test_id == test_id
    ).delete(synchronize_session=False)

    db.delete(test)
    db.commit()

    return {"message": "Test deleted successfully"}


# ======================================================
# SUBMIT TEST / GENERATE REPORT
# ======================================================

@router.post("/{test_id}/submit")
def submit_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    test = db.query(models.Test).filter(models.Test.id == test_id).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    answers = db.query(models.QuestionAnswer)\
        .join(models.Question, models.Question.id == models.QuestionAnswer.question_id)\
        .filter(
            models.Question.test_id == test_id,
            models.QuestionAnswer.user_id == current_user.id
        ).all()

    scores = [a.final_score for a in answers if a.final_score is not None]
    grammar_scores = [a.grammar_score for a in answers if a.grammar_score is not None]
    fluency_scores = [a.fluency_score for a in answers if a.fluency_score is not None]

    avg_score = round(sum(scores) / len(scores), 2) if scores else 0
    avg_grammar = round(sum(grammar_scores) / len(grammar_scores), 2) if grammar_scores else 0
    avg_fluency = round(sum(fluency_scores) / len(fluency_scores), 2) if fluency_scores else 0

    if avg_score >= 9:
        level = "Expert"
    elif avg_score >= 7:
        level = "Advanced"
    elif avg_score >= 5:
        level = "Intermediate"
    else:
        level = "Beginner"

    suggestions = []

    if avg_fluency < 7:
        suggestions.append("Try to speak more smoothly and avoid long pauses.")

    if avg_grammar < 7:
        suggestions.append("Work on improving grammar accuracy.")

    if avg_score >= 8:
        suggestions.append("Great job! Try using more advanced vocabulary.")

    if not suggestions:
        suggestions.append("Keep practicing regularly to improve your speaking skills.")

    report = {
        "overall_score": avg_score,
        "average_grammar": avg_grammar,
        "average_fluency": avg_fluency,
        "level": level,
        "suggestions": suggestions
    }

    result = models.Result(
        user_id=current_user.id,
        test_id=test_id,
        score=avg_score,
        evaluation=report,
        answers=[
            {
                "question_id": a.question_id,
                "written_answer": a.written_answer,
                "transcribed_text": a.transcribed_text,
                "final_score": a.final_score
            }
            for a in answers
        ]
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    return {**report, "result_id": result.id, "answers_count": len(answers)}

@router.get("/me/results")
def get_my_results(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    answers = db.query(models.QuestionAnswer)\
        .filter(models.QuestionAnswer.user_id == current_user.id)\
        .order_by(models.QuestionAnswer.created_at.desc())\
        .all()

    result = []

    for ans in answers:

        question = db.query(models.Question).filter(
            models.Question.id == ans.question_id
        ).first()

        result.append({
            "id": ans.id,
            "question_id": ans.question_id,
            "question_text": question.question_text if question else None,
            "score": ans.final_score,
            "grammar_score": ans.grammar_score,
            "fluency_score": ans.fluency_score,
            "word_count": ans.word_count,
            "feedback": ans.feedback,
            "created_at": ans.created_at
        })

    return result


# from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
# from app.services.ai_scoring import transcribe_audio, evaluate_answer
# from sqlalchemy.orm import Session
# from sqlalchemy import text
# from ..models import Test
# from typing import List
# import os
# import shutil
# from datetime import datetime

# # Try to import librosa for audio duration, but make it optional
# try:
#     import librosa
#     LIBROSA_AVAILABLE = True
#     print("✅ librosa imported successfully - audio duration analysis enabled")
# except ImportError:
#     LIBROSA_AVAILABLE = False
#     print("⚠️ librosa not available - audio duration analysis disabled")

# # IMPORTANT: tell whisper where ffmpeg is
# os.environ["PATH"] += os.pathsep + r"C:\ffmpeg-8.0.1-essentials_build\bin"

# from ..database import SessionLocal
# from ..services.auth_service import get_current_admin, get_current_user
# from .. import models, schemas


# router = APIRouter(
#     prefix="/tests",
#     tags=["Tests"]
# )

# UPLOAD_DIR = "uploads"

# if not os.path.exists(UPLOAD_DIR):
#     os.makedirs(UPLOAD_DIR)
# # ================= DATABASE =================

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # ======================================================
# # GET ALL TESTS (PUBLIC)
# # ======================================================

# @router.get("/", response_model=List[schemas.TestResponse])
# def get_tests(db: Session = Depends(get_db)):
#     return db.query(models.Test).all()


# # ======================================================
# # CREATE TEST (ADMIN ONLY)
# # ======================================================

# @router.post("/", response_model=schemas.TestResponse)
# def create_test(
#     test: schemas.TestCreate,
#     db: Session = Depends(get_db),
#     current_admin = Depends(get_current_admin)
# ):
#     new_test = models.Test(
#         title=test.title,
#         description=test.description
#     )

#     db.add(new_test)
#     db.commit()
#     db.refresh(new_test)

#     return new_test


# # ======================================================
# # ADD QUESTION (ADMIN ONLY)
# # ======================================================

# @router.post("/{test_id}/questions", response_model=schemas.QuestionResponse)
# def add_question(
#     test_id: int,
#     question: schemas.QuestionCreate,
#     db: Session = Depends(get_db),
#     current_admin = Depends(get_current_admin)
# ):

#     test = db.query(models.Test).filter(models.Test.id == test_id).first()

#     if not test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     new_question = models.Question(
#         question_text=question.question_text,
#         question_type=question.question_type,
#         time_limit=question.time_limit,
#         order_number=question.order_number,
#         test_id=test_id
#     )

#     db.add(new_question)
#     db.commit()
#     db.refresh(new_question)

#     return new_question


# # ======================================================
# # GET SINGLE TEST WITH QUESTIONS
# # ======================================================

# @router.get("/{test_id}", response_model=schemas.TestResponse)
# def get_test(test_id: int, db: Session = Depends(get_db)):

#     test = db.query(models.Test).filter(models.Test.id == test_id).first()

#     if not test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     return test


# # ======================================================
# # SUBMIT FULL TEST
# # ======================================================

# @router.post("/{test_id}/submit", response_model=schemas.ResultResponse)
# def submit_test(
#     test_id: int,
#     submission: schemas.SubmitTest,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):

#     test = db.query(models.Test).filter(models.Test.id == test_id).first()

#     if not test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     answers = db.query(models.QuestionAnswer).join(models.Question).filter(
#         models.Question.test_id == test_id,
#         models.QuestionAnswer.user_id == current_user.id
#     ).all()

#     scores = [a.final_score for a in answers if a.final_score is not None]
#     grammar_scores = [a.grammar_score for a in answers if a.grammar_score is not None]
#     fluency_scores = [a.fluency_score for a in answers if a.fluency_score is not None]

#     avg_score = sum(scores) / len(scores) if scores else 0
#     avg_grammar = sum(grammar_scores) / len(grammar_scores) if grammar_scores else 0
#     avg_fluency = sum(fluency_scores) / len(fluency_scores) if fluency_scores else 0
    
#     if avg_score >=9:
#         level = "Expert"
#     elif avg_score >=7:
#         level = "Advanced"
#     elif avg_score >=5:
#         level = "Intermediate"
#     else:
#         level = "Beginner"

#     suggestions = []
    
#     if avg_fluency < 7:
#         suggestions.append("Try to speak more smoothly and avoid long pauses.")

#     if avg_grammar < 7:
#         suggestions.append("Work on improving grammar accuracy.")

#     if avg_score >= 8:
#         suggestions.append("Great job! Try using more advanced vocabulary.")

#     if not suggestions:
#         suggestions.append("Keep practicing regularly to improve your speaking skills.")

#     formatted_answers = [
#         {
#             "question_id": ans.question_id,
#             "written_answer": ans.written_answer,
#             "audio_path": ans.audio_path
#         }
#         for ans in answers
#     ]

#     result = models.Result(
#         user_id=current_user.id,
#         test_id=test_id,
#         score=round(avg_score, 2),
#         evaluation={
#             "average_grammar": round(avg_grammar,2),
#             "average_fluency": round(avg_fluency,2),
#             "level": level,
#             "suggestions": suggestions
#         },
#         answers=formatted_answers
#     )

#     db.add(result)
#     db.commit()
#     db.refresh(result)

#     return result


# # ======================================================
# # SUBMIT SINGLE QUESTION
# # ======================================================

# @router.post("/questions/{question_id}/submit")
# def submit_question(
#     question_id: int,
#     data: dict,
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):

#     question = db.query(models.Question)\
#         .filter(models.Question.id == question_id)\
#         .first()

#     if not question:
#         raise HTTPException(status_code=404, detail="Question not found")

#     answer = models.QuestionAnswer(
#         user_id=current_user.id,
#         question_id=question_id,
#         written_answer=data.get("written_answer"),
#         audio_path=data.get("audio_path")
#     )

#     db.add(answer)
#     db.commit()
#     db.refresh(answer)

#     return {"message": "Answer saved successfully"}


# # ======================================================
# # GET MY ANSWERS
# # ======================================================

# @router.get("/me/answers")
# def get_my_answers(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):

#     answers = db.query(models.QuestionAnswer)\
#         .filter(models.QuestionAnswer.user_id == current_user.id)\
#         .all()

#     grouped = {}

#     for ans in answers:

#         question = ans.question
#         if not question:
#             continue

#         test = question.test
#         if not test:
#             continue

#         if test.id not in grouped:
#             grouped[test.id] = {
#                 "test_id": test.id,
#                 "test_title": test.title,
#                 "answers": []
#             }

#         grouped[test.id]["answers"].append({
#             "question_id": question.id,
#             "question_text": question.question_text,
#             "written_answer": ans.written_answer,
#             "submitted_at": ans.submitted_at
#         })

#     return list(grouped.values())


# # ======================================================
# # DASHBOARD STATS
# # ======================================================

# @router.get("/me/dashboard")
# def get_dashboard_stats(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):

#     answers = db.query(models.QuestionAnswer)\
#         .filter(models.QuestionAnswer.user_id == current_user.id)\
#         .all()

#     total_answers = len(answers)

#     if total_answers == 0:
#         return {
#             "total_tests": 0,
#             "total_answers": 0,
#             "total_words": 0,
#             "avg_words": 0,
#             "fluency_score": 0,
#             "fluency_level": "Beginner",
#             "last_attempt": None
#         }

#     total_words = 0
#     test_ids = set()
#     last_attempt = None

#     for ans in answers:

#         if not ans.question:
#             continue

#         words = len(ans.written_answer.split()) if ans.written_answer else 0
#         total_words += words

#         test_ids.add(ans.question.test_id)

#         if not last_attempt or ans.submitted_at > last_attempt:
#             last_attempt = ans.submitted_at

#     avg_words = total_words / total_answers

#     # WORD SCORE
#     if avg_words < 15:
#         word_score = 20
#     elif avg_words < 30:
#         word_score = 40
#     elif avg_words < 60:
#         word_score = 60
#     else:
#         word_score = 70

#     # CONSISTENCY SCORE
#     if total_answers < 3:
#         consistency_score = 5
#     elif total_answers < 8:
#         consistency_score = 15
#     elif total_answers < 16:
#         consistency_score = 25
#     else:
#         consistency_score = 30

#     fluency_score = word_score + consistency_score

#     if fluency_score <= 40:
#         fluency_level = "Beginner"
#     elif fluency_score <= 70:
#         fluency_level = "Intermediate"
#     elif fluency_score <= 85:
#         fluency_level = "Upper Intermediate"
#     else:
#         fluency_level = "Advanced"

#     return {
#         "total_tests": len(test_ids),
#         "total_answers": total_answers,
#         "total_words": total_words,
#         "avg_words": round(avg_words, 2),
#         "fluency_score": fluency_score,
#         "fluency_level": fluency_level,
#         "last_attempt": last_attempt
#     }


# # ======================================================
# # ADMIN ANALYTICS
# # ======================================================

# @router.get("/admin/analytics")
# def get_admin_analytics(
#     db: Session = Depends(get_db),
#     current_admin: str = Depends(get_current_admin)
# ):

#     total_users = db.query(models.User).count()
#     total_tests = db.query(models.Test).count()
#     total_questions = db.query(models.Question).count()
#     total_answers = db.query(models.QuestionAnswer).count()

#     return {
#         "total_users": total_users,
#         "total_tests": total_tests,
#         "total_questions": total_questions,
#         "total_answers": total_answers
#     }


# # ======================================================
# # ADMIN USERS
# # ======================================================

# @router.get("/admin/users")
# def get_all_users(
#     db: Session = Depends(get_db),
#     current_admin: str = Depends(get_current_admin)
# ):

#     users = db.query(models.User).all()

#     return [
#         {
#             "id": user.id,
#             "email": user.email,
#             "role": user.role
#         }
#         for user in users
#     ]

# @router.delete("/{test_id}")
# def delete_test(test_id: int, db: Session = Depends(get_db), current_admin = Depends(get_current_admin)):

#     test = db.query(models.Test).filter(models.Test.id == test_id).first()

#     if not test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     # Delete related data first (to handle foreign key constraints)
#     try:
#         # Delete related questions
#         questions = db.query(models.Question).filter(models.Question.test_id == test_id).all()
#         for question in questions:
#             # Delete related answers for each question
#             try:
#                 related_answers = db.query(models.QuestionAnswer).filter(
#                     models.QuestionAnswer.question_id == question.id
#                 ).all()
#                 for answer in related_answers:
#                     db.delete(answer)
#             except:
#                 pass
            
#             try:
#                 db.execute(text(f"DELETE FROM answers WHERE question_id = :qid"), {"qid": question.id})
#             except:
#                 pass
            
#             db.delete(question)
        
#         # Delete related results
#         try:
#             db.execute(text(f"DELETE FROM results WHERE test_id = :tid"), {"tid": test_id})
#         except:
#             pass
        
#         # Delete related attempts
#         try:
#             attempts = db.query(models.Attempt).filter(models.Attempt.test_id == test_id).all()
#             for attempt in attempts:
#                 db.delete(attempt)
#         except:
#             pass
        
#         # Commit all the related deletions first
#         db.commit()
        
#         # Now delete the test
#         db.delete(test)
#         db.commit()
        
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Failed to delete test: {str(e)}")

#     return {"message": "Test deleted successfully"}

# @router.get("/{test_id}/questions")
# def get_questions(
#     test_id: int,
#     db: Session = Depends(get_db),
#     current_user = Depends(get_current_user)
# ):

#     questions = db.query(models.Question).filter(
#         models.Question.test_id == test_id
#     ).all()

#     return questions

# @router.put("/{test_id}/questions/{question_id}")
# def update_question(
#     test_id: int,
#     question_id: int,
#     question: schemas.QuestionCreate,
#     db: Session = Depends(get_db),
#     current_admin = Depends(get_current_admin)
# ):
    
#     # Verify question belongs to the specified test
#     existing_question = db.query(models.Question).filter(
#         models.Question.id == question_id,
#         models.Question.test_id == test_id
#     ).first()
    
#     if not existing_question:
#         raise HTTPException(status_code=404, detail="Question not found")
    
#     # Update question
#     existing_question.question_text = question.question_text
#     existing_question.time_limit = question.time_limit
#     existing_question.question_type = question.question_type
#     existing_question.order_number = question.order_number
    
#     db.commit()
#     db.refresh(existing_question)
    
#     return existing_question

# @router.delete("/{test_id}/questions/{question_id}")
# def delete_question(
#     test_id: int,
#     question_id: int,
#     db: Session = Depends(get_db),
#     current_admin = Depends(get_current_admin)
# ):
    
#     # Verify question belongs to the specified test
#     existing_question = db.query(models.Question).filter(
#         models.Question.id == question_id,
#         models.Question.test_id == test_id
#     ).first()
    
#     if not existing_question:
#         raise HTTPException(status_code=404, detail="Question not found")
    
#     # Delete related answers first (to handle foreign key constraint)
#     # Handle both possible answer tables
#     try:
#         # Try question_answers table first
#         related_answers = db.query(models.QuestionAnswer).filter(
#             models.QuestionAnswer.question_id == question_id
#         ).all()
        
#         for answer in related_answers:
#             db.delete(answer)
#     except Exception as e:
#         print(f"Error with question_answers: {e}")
    
#     # Also try to delete from answers table if it exists
#     try:
#         result = db.execute(text(f"DELETE FROM answers WHERE question_id = :qid"), {"qid": question_id})
#         print(f"Deleted {result.rowcount} rows from answers table")
#     except Exception as e:
#         print(f"Error with answers table: {e}")
    
#     # Commit the answer deletions first
#     db.commit()
    
#     # Now delete the question
#     db.delete(existing_question)
#     db.commit()
    
#     return {"message": "Question deleted successfully"}

# @router.put("/{test_id}")
# def update_test(
#     test_id: int,
#     test: schemas.TestCreate,
#     db: Session = Depends(get_db),
#     current_admin = Depends(get_current_admin)
# ):

#     existing_test = db.query(models.Test).filter(models.Test.id == test_id).first()

#     if not existing_test:
#         raise HTTPException(status_code=404, detail="Test not found")

#     existing_test.title = test.title
#     existing_test.description = test.description

#     db.commit()
#     db.refresh(existing_test)

#     return existing_test

# @router.post("/submit-audio")
# async def submit_audio(
#     file: UploadFile = File(...),
# ):

#     file_location = f"recordings/{file.filename}"

#     with open(file_location, "wb") as buffer:
#         buffer.write(await file.read())

#     return {"message": "Audio uploaded"}

# @router.post("/submit-answer/{question_id}")
# async def submit_answer(
#     question_id: int,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db),
#     user = Depends(get_current_user)
# ):
#     if not os.path.exists(UPLOAD_DIR):
#         os.makedirs(UPLOAD_DIR)

#     filename = f"{datetime.now().timestamp()}_{file.filename}"

#     filepath = os.path.join(UPLOAD_DIR, filename)

#     with open(filepath, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     try:
#         text_answer, audio_duration = transcribe_audio(filepath)
        
#         # Audio duration is now handled in transcribe_audio function
#         print(f"Audio duration from transcribe_audio: {audio_duration}")
            
#     except Exception as e:
#         print("Whisper error:", e)
#         return {"error": "Audio transcription failed"}

#     question = db.query(models.Question).filter(models.Question.id == question_id).first()
#     if not question:
#         return {"error": "Question not found"}

#     evaluation = evaluate_answer(question.question_text, text_answer, audio_duration)
    
#     answer = models.QuestionAnswer(
#         user_id=user.id,
#         question_id=question_id,
#         written_answer=None,  # For text-based answers only
#         audio_path=filepath,
#         transcribed_text=text_answer,  # Store transcribed audio here
#         grammar_score=evaluation.get("grammar_score"),
#         fluency_score=evaluation.get("fluency_score"),
#         final_score=evaluation.get("final_score"),
#         grammar_errors=evaluation.get("grammar_errors", 0),  # Get from evaluation or default to 0
#         word_count=evaluation.get("word_count", 0),  # Store word count
#         feedback=evaluation.get("feedback")
#     )

#     db.add(answer)
#     db.commit()

#     return {
#         "message": "Audio uploaded and processed",
#         "grammar_score": evaluation.get("grammar_score"),
#         "fluency_score": evaluation.get("fluency_score"),
#         "final_score": evaluation.get("final_score"),
#         "performance_level": evaluation.get("performance_level"),
#         "feedback": evaluation.get("feedback"),
#         "word_count": evaluation.get("word_count"),
#         "is_silent": evaluation.get("is_silent", False)
#     }

# @router.get("/admin/attempts")
# def get_attempts(db: Session = Depends(get_db)):

#     attempts = db.query(models.Attempt).all()

#     result = []

#     for a in attempts:
#         user = db.query(models.User).filter(models.User.id == a.user_id).first()
#         test = db.query(models.Test).filter(models.Test.id == a.test_id).first()

#         result.append({
#             "attempt_id": a.id,
#             "user": user.email if user else "Unknown",
#             "test": test.title if test else "Unknown",
#             "date": a.created_at
#         })

#     return result

# @router.post("/submit-text-answer/{question_id}")
# def submit_text_answer(
#     question_id: int, 
#     data: schemas.TextAnswer, 
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):

#     question = db.query(models.Question).filter(models.Question.id == question_id).first()
#     if not question:
#         raise HTTPException(status_code=404, detail="Question not found")

#     # Evaluate the text answer using the same AI scoring as audio
#     evaluation = evaluate_answer(question.question_text, data.answer, audio_duration=None, answer_type="text")
    
#     answer = models.QuestionAnswer(
#         user_id=current_user.id,
#         question_id=question_id,
#         written_answer=data.answer,
#         audio_path=None,
#         transcribed_text=data.answer,  # Store the text answer as transcribed text
#         grammar_score=evaluation.get("grammar_score"),
#         fluency_score=evaluation.get("fluency_score"),
#         final_score=evaluation.get("final_score"),
#         grammar_errors=evaluation.get("grammar_errors", 0),
#         word_count=evaluation.get("word_count", 0),
#         feedback=evaluation.get("feedback")
#     )

#     db.add(answer)
#     db.commit()
#     db.refresh(answer)

#     return {
#         "message": "Text answer submitted and evaluated successfully",
#         "answer_id": answer.id,
#         "grammar_score": evaluation.get("grammar_score"),
#         "fluency_score": evaluation.get("fluency_score"),
#         "final_score": evaluation.get("final_score"),
#         "performance_level": evaluation.get("performance_level"),
#         "feedback": evaluation.get("feedback"),
#         "word_count": evaluation.get("word_count"),
#         "is_silent": evaluation.get("is_silent", False)
#     }

# @router.get("/me/dashboard")
# def get_user_dashboard_stats(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     """Get user's dashboard statistics"""
    
#     # Get all user's answers
#     answers = db.query(models.QuestionAnswer).filter(
#         models.QuestionAnswer.user_id == current_user.id
#     ).all()
    
#     if not answers:
#         return {
#             "tests_completed": 0,
#             "average_score": 0,
#             "level": "Beginner"
#         }
    
#     # Calculate stats
#     total_tests = len(answers)
#     avg_score = round(sum(ans.final_score or 0 for ans in answers) / total_tests, 1)
    
#     # Determine level based on average score
#     if avg_score >= 9:
#         level = "Expert"
#     elif avg_score >= 8:
#         level = "Advanced"
#     elif avg_score >= 7:
#         level = "Upper-Intermediate"
#     elif avg_score >= 6:
#         level = "Intermediate"
#     elif avg_score >= 4:
#         level = "Beginner"
#     else:
#         level = "Novice"
    
#     return {
#         "tests_completed": total_tests,
#         "average_score": avg_score,
#         "level": level
#     }

# @router.get("/admin/analytics")
# def get_admin_analytics(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_admin)
# ):
#     """Get admin analytics data"""
    
#     # Get all users and their test attempts
#     users = db.query(models.User).all()
    
#     # Get all tests
#     tests = db.query(models.Test).all()
    
#     # Get all answers for statistics
#     answers = db.query(models.QuestionAnswer).all()
    
#     # Calculate statistics
#     total_users = len(users)
#     total_tests = len(tests)
#     total_attempts = len(answers)
    
#     # Calculate average score
#     avg_score = 0
#     if answers:
#         avg_score = round(sum(ans.final_score or 0 for ans in answers) / len(answers), 1)
    
#     # Calculate tests per user
#     user_stats = []
#     for user in users:
#         user_answers = db.query(models.QuestionAnswer).filter(models.QuestionAnswer.user_id == user.id).all()
#         user_attempts = len(user_answers)
#         user_avg = 0
#         if user_answers:
#             user_avg = round(sum(ans.final_score or 0 for ans in user_answers) / len(user_answers), 1)
        
#         user_stats.append({
#             "email": user.email,
#             "attempts": user_attempts,
#             "average_score": user_avg
#         })
    
#     return {
#         "total_users": total_users,
#         "total_tests": total_tests,
#         "total_attempts": total_attempts,
#         "overall_average": avg_score,
#         "users": user_stats
#     }

# @router.get("/me/answers")
# def get_user_recent_answers(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(get_current_user)
# ):
#     """Get user's recent answers"""
    
#     answers = db.query(models.QuestionAnswer).filter(
#         models.QuestionAnswer.user_id == current_user.id
#     ).order_by(models.QuestionAnswer.created_at.desc()).limit(10).all()
    
#     result = []
#     for answer in answers:
#         result.append({
#             "id": answer.id,
#             "question_id": answer.question_id,
#             "final_score": answer.final_score,
#             "word_count": answer.word_count,
#             "created_at": answer.created_at.isoformat() if answer.created_at else None,
#             "question_text": answer.question.question_text if answer.question else None
#         })
    
#     return result