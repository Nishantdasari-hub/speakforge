from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List
import os

from ..database import SessionLocal
from ..services.auth_service import get_current_admin, get_current_user
from .. import models, schemas
from app.services.ai_scoring import process_ai_scoring, process_text_scoring


router = APIRouter(
    prefix="/tests",
    tags=["Tests"]
)

from app.config import UPLOAD_DIR

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
    current_admin=Depends(get_current_admin)
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

@router.get("/{test_id:int}", response_model=schemas.TestResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):

    test = db.query(models.Test).filter(models.Test.id == test_id).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    return test


# ======================================================
# ADD QUESTION (ADMIN)
# ======================================================

@router.post("/{test_id:int}/questions", response_model=schemas.QuestionResponse)
def add_question(
    test_id: int,
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
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

@router.get("/{test_id:int}/questions")
def get_questions(
    test_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    questions = db.query(models.Question).filter(
        models.Question.test_id == test_id
    ).all()

    return questions


# ======================================================
# SUBMIT ANSWER (AUDIO OR TEXT)
# ======================================================

@router.post("/submit-answer/{question_id}")
async def submit_answer(
    question_id: int,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(None), 
    text_answer: str = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    question = db.query(models.Question).filter(
        models.Question.id == question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    answer = models.QuestionAnswer(
        user_id=current_user.id,
        question_id=question_id
    )

    db.add(answer)
    db.commit()
    db.refresh(answer)

    # ================= AUDIO =================
    if audio:
        audio_path = f"{UPLOAD_DIR}/{answer.id}.webm"

        with open(audio_path, "wb") as f:
            f.write(await audio.read())

        answer.audio_path = audio_path
        db.commit()


    # ================= TEXT =================
    if text_answer:

        answer.written_answer = text_answer
        db.commit()



    return {"message": "Answer submitted successfully"}

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

@router.get("/me/answers")
def get_user_recent_answers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    answers = db.query(models.QuestionAnswer).filter(
        models.QuestionAnswer.user_id == current_user.id
    ).order_by(models.QuestionAnswer.id.desc()).limit(10).all()

    result = []

    for answer in answers:
        result.append({
            "id": answer.id,
            "question_id": answer.question_id,
            "final_score": answer.final_score,
            "word_count": answer.word_count,
            "created_at": answer.created_at.isoformat() if answer.created_at else None
        })

    return result


# ======================================================
# USER RESULTS (FOR MY RESULTS PAGE)
# ======================================================

@router.get("/me/results")
def get_user_results(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    # Get all answers grouped by test
    answers = db.query(models.QuestionAnswer).filter(
        models.QuestionAnswer.user_id == current_user.id
    ).order_by(models.QuestionAnswer.id.desc()).all()

    # Group by test_id
    test_results = {}
    for answer in answers:
        question = db.query(models.Question).filter(
            models.Question.id == answer.question_id
        ).first()
        
        if question and question.test_id:
            if question.test_id not in test_results:
                test_results[question.test_id] = {
                    "test_id": question.test_id,
                    "score": 0,
                    "created_at": answer.created_at.isoformat() if answer.created_at else None,
                    "answers": []
                }
            
            test_results[question.test_id]["answers"].append({
                "question_id": answer.question_id,
                "written_answer": answer.written_answer
            })
            
            if answer.final_score:
                test_results[question.test_id]["score"] = max(
                    test_results[question.test_id]["score"], 
                    answer.final_score
                )

    return list(test_results.values())

# ======================================================
# SUBMIT TEST (RUN AI SCORING IN BACKGROUND)
# ======================================================

@router.post("/{test_id:int}/submit")
def submit_test(
    test_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):

    answers = (
        db.query(models.QuestionAnswer)
        .join(models.Question, models.Question.id == models.QuestionAnswer.question_id)
        .filter(
            models.QuestionAnswer.user_id == current_user.id,
            models.Question.test_id == test_id
        )
        .all()
    )

    for answer in answers:

        # TEXT ANSWER
        if answer.written_answer:
            background_tasks.add_task(
                process_text_scoring,
                answer.id,
                answer.question.question_text,
                answer.written_answer
            )

        # AUDIO ANSWER
        if answer.audio_path:
            background_tasks.add_task(
                process_ai_scoring,
                answer.id,
                answer.question.question_text,
                answer.audio_path
            )

    return {
        "message": "Test submitted successfully",
        "status": "AI evaluation running in background"
    }

# ======================================================
# ADMIN DASHBOARD ANALYTICS
# ======================================================

@router.get("/admin/analytics")
def admin_analytics(
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin)
):

    total_tests = db.query(models.Test).count()

    total_users = db.query(models.User).count()

    total_questions = (
        db.query(models.Question)
        .join(models.Test, models.Test.id == models.Question.test_id)
        .count()
    )

    total_attempts = (
        db.query(models.QuestionAnswer)
        .join(models.Question, models.Question.id == models.QuestionAnswer.question_id)
        .count()
    )

    return {
        "total_tests": total_tests,
        "total_questions": total_questions,
        "total_users": total_users,
        "total_attempts": total_attempts
    }

# ======================================================
# UPDATE TEST (ADMIN)
# ======================================================

@router.put("/{test_id:int}", response_model=schemas.TestResponse)
def update_test(
    test_id: int,
    test: schemas.TestCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):

    db_test = db.query(models.Test).filter(models.Test.id == test_id).first()

    if not db_test:
        raise HTTPException(status_code=404, detail="Test not found")

    db_test.title = test.title
    db_test.description = test.description

    db.commit()
    db.refresh(db_test)

    return db_test

# ======================================================
# DELETE TEST (ADMIN)
# ======================================================

@router.delete("/{test_id:int}")
def delete_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):

    test = db.query(models.Test).filter(models.Test.id == test_id).first()

    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    db.delete(test)
    db.commit()

    return {"message": "Test deleted successfully"}

# ======================================================
# UPDATE QUESTION (ADMIN)
# ======================================================

@router.put("/{test_id:int}/questions/{question_id}")
def update_question(
    test_id: int,
    question_id: int,
    question: schemas.QuestionCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):

    db_question = db.query(models.Question).filter(
        models.Question.id == question_id,
        models.Question.test_id == test_id
    ).first()

    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")

    db_question.question_text = question.question_text
    db_question.question_type = question.question_type
    db_question.time_limit = question.time_limit
    db_question.order_number = question.order_number

    db.commit()
    db.refresh(db_question)

    return db_question

# ======================================================
# DELETE QUESTION (ADMIN)
# ======================================================

@router.delete("/{test_id:int}/questions/{question_id}")
def delete_question(
    test_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):

    question = db.query(models.Question).filter(
        models.Question.id == question_id,
        models.Question.test_id == test_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(question)
    db.commit()

    return {"message": "Question deleted successfully"}