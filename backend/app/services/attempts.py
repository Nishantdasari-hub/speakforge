from fastapi import HTTPException
from app import models
from app.services.ai_scoring import RUBRIC


def get_attempt(db, attempt_id, user_id, lock=False):
    query = db.query(models.Attempt).filter_by(id=attempt_id, user_id=user_id)
    if lock:
        query = query.with_for_update()
    attempt = query.first()
    if not attempt:
        raise HTTPException(404, "Attempt not found")
    return attempt


def summarize(attempt):
    answers = attempt.answers
    if not attempt.submitted_at:
        state = "draft"
    elif any(a.score_status == "failed" for a in answers):
        state = "failed"
    elif not answers or any(a.score_status != "completed" for a in answers):
        state = "processing"
    else:
        state = "completed"
    complete = state == "completed"
    average = lambda field: round(sum(getattr(a, field) or 0 for a in answers) / len(answers), 1) if complete else None
    score = average("final_score")
    level = "Advanced practice" if score is not None and score >= 8 else "Developing practice"
    return {
        "attempt_id":attempt.id, "test_id":attempt.test_id, "title":attempt.test.title,
        "status":state, "overall_score":score, "score":score,
        "average_grammar":average("grammar_score"), "average_fluency":average("fluency_score"),
        "level":level if complete else state.capitalize(),
        "created_at":attempt.created_at.isoformat(), "rubric":RUBRIC,
        "scoring_note":"Practice estimate from grammar, response length and pace. Does not assess relevance, pronunciation or an official exam band.",
        "suggestions":list(dict.fromkeys(a.feedback for a in answers if a.feedback)) if complete else [],
        "answers":[{"question_id":a.question_id,"question_text":a.question.question_text,
                    "written_answer":a.written_answer,"transcript":a.transcribed_text,
                    "fluency":a.fluency_score,"grammar":a.grammar_score,"score":a.final_score,
                    "grammar_errors":a.grammar_errors,"word_count":a.word_count,
                    "feedback":a.feedback,"status":a.score_status,"error":a.score_error} for a in answers],
    }
