"""Durable database queue. Run separately with python -m app.worker."""
import logging
import signal
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import and_, or_
from app import models
from app.database import SessionLocal
from app.services.ai_scoring import evaluate_answer, transcribe_audio, get_language_tool

logger = logging.getLogger(__name__)
MAX_TRIES = 3
LEASE_SECONDS = 600
HEARTBEAT = Path("/tmp/speakforge-worker-heartbeat")


def claim_job():
    now = datetime.utcnow()
    with SessionLocal() as db:
        answer = db.query(models.QuestionAnswer).filter(or_(
            models.QuestionAnswer.score_status == "queued",
            and_(models.QuestionAnswer.score_status == "processing",
                 models.QuestionAnswer.score_started_at < now - timedelta(seconds=LEASE_SECONDS)),
        )).order_by(models.QuestionAnswer.id).with_for_update(skip_locked=True).first()
        if not answer:
            return None
        if answer.score_attempts >= MAX_TRIES:
            answer.score_status = "failed"
            answer.score_error = "Evaluation could not finish. Please retry."
            db.commit()
            return None
        answer.score_status = "processing"
        answer.score_attempts += 1
        answer.score_started_at = now
        answer.score_token = str(uuid.uuid4())
        job = {"id":answer.id,"token":answer.score_token,"question":answer.question.question_text,
               "audio":answer.audio_path,"text":answer.written_answer,"tries":answer.score_attempts}
        db.commit()
        return job


def run_job(job):
    try:
        if job["audio"]:
            transcript, duration = transcribe_audio(job["audio"])
            result = evaluate_answer(job["question"], transcript, duration, "audio")
        else:
            transcript = job["text"] or ""
            result = evaluate_answer(job["question"], transcript, answer_type="text")
        changes = dict(result, transcribed_text=transcript, score_status="completed", score_error=None)
    except Exception:
        logger.exception("Scoring failed for answer %s (attempt %s)", job["id"], job["tries"])
        get_language_tool.cache_clear()
        changes = {"score_status":"failed" if job["tries"] >= MAX_TRIES else "queued",
                   "score_error":"Evaluation is temporarily unavailable. Please retry if it fails."}
    with SessionLocal() as db:
        # A worker recovering an expired lease must not be overwritten by an old worker.
        db.query(models.QuestionAnswer).filter_by(id=job["id"], score_token=job["token"], score_status="processing").update(changes)
        db.commit()


def main():
    logging.basicConfig(level=logging.INFO)
    stopping = False
    def stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping:
        HEARTBEAT.touch()
        try:
            job = claim_job()
            if job:
                run_job(job)
            else:
                time.sleep(1)
        except Exception:
            logger.exception("Scoring queue unavailable")
            time.sleep(5)
    HEARTBEAT.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
