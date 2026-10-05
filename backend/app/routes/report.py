from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.services.auth_service import get_current_user
from app.services.attempts import get_attempt, summarize

router = APIRouter()


@router.get("/report/{test_id}")
def get_test_report(test_id: int, attempt_id: int | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if attempt_id is not None:
        attempt = get_attempt(db, attempt_id, user.id)
    else:
        attempt = db.query(models.Attempt).filter(models.Attempt.user_id == user.id, models.Attempt.test_id == test_id, models.Attempt.submitted_at.isnot(None)).order_by(models.Attempt.id.desc()).first()
    if not attempt or attempt.test_id != test_id:
        raise HTTPException(404, "No submitted attempt found for this test")
    return summarize(attempt)
