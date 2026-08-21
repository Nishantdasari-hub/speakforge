from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.services.auth_service import get_current_user
from app.models import User

router = APIRouter()


@router.get("/report/{test_id}")
def get_test_report(
    test_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    answers = (
        db.query(models.QuestionAnswer)
        .join(models.Question, models.Question.id == models.QuestionAnswer.question_id)
        .filter(
            models.QuestionAnswer.user_id == user.id,
            models.Question.test_id == test_id
        )
        .all()
    )

    if not answers:
        return {
            "overall_score": 0,
            "average_fluency": 0,
            "average_grammar": 0,
            "level": "Evaluating...",
            "answers": []
        }

    # WAIT until ALL answers are evaluated
    for a in answers:
        if a.final_score is None:
            return {
                "overall_score": 0,
                "average_fluency": 0,
                "average_grammar": 0,
                "level": "Evaluating...",
                "answers": []
            }

    grammar_scores = [a.grammar_score for a in answers]
    fluency_scores = [a.fluency_score for a in answers]
    final_scores = [a.final_score for a in answers]

    avg_grammar = round(sum(grammar_scores) / len(grammar_scores), 1)
    avg_fluency = round(sum(fluency_scores) / len(fluency_scores), 1)
    overall = round(sum(final_scores) / len(final_scores), 1)

    if overall >= 9:
        level = "Expert"
    elif overall >= 8:
        level = "Advanced"
    elif overall >= 7:
        level = "Upper Intermediate"
    elif overall >= 6:
        level = "Intermediate"
    else:
        level = "Beginner"

    answers_data = []

    for a in answers:
        answers_data.append({
            "question_id": a.question_id,
            "transcript": a.transcribed_text,
            "fluency": a.fluency_score,
            "grammar": a.grammar_score,
            "score": a.final_score,
            "feedback": a.feedback
        })

    return {
        "overall_score": overall,
        "average_fluency": avg_fluency,
        "average_grammar": avg_grammar,
        "level": level,
        "answers": answers_data
    }