from sqlalchemy.orm import Session
from .. import models
from datetime import datetime

def create_test(db: Session, title: str, description: str):
    new_test = models.Test(
        title=title,
        description=description
    )
    db.add(new_test)
    db.commit()
    db.refresh(new_test)
    return new_test


def add_question(db: Session, test_id: int, question_text: str):
    new_question = models.Question(
        question_text=question_text,
        test_id=test_id
    )
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return new_question


def get_all_tests(db: Session):
    return db.query(models.Test).all()


def get_test_with_questions(db: Session, test_id: int):
    return db.query(models.Test).filter(models.Test.id == test_id).first()

def evaluate_answers(answers: list[str]):
    
    total_score = 0
    fluency_total = 0
    vocab_total = 0
    grammar_total = 0

    for answer in answers:
        word_count = len(answer.split())

        fluency = min(word_count * 2, 40)
        vocabulary = 15 if len(set(answer.split())) > 15 else 10
        grammar = 15  # placeholder

        fluency_total += fluency
        vocab_total += vocabulary
        grammar_total += grammar

    total_score = min(fluency_total + vocab_total + grammar_total, 100)

    return {
        "score": total_score,
        "fluency": fluency_total,
        "vocabulary": vocab_total,
        "grammar": grammar_total,
        "feedback": "Good response. Try adding more structured examples."
    }

def submit_test(db: Session, user_id: int, test_id: int, answers: list[str]):

    evaluation_data = evaluate_answers(answers)

    new_result = models.Result(
        user_id=user_id,
        test_id=test_id,
        score=evaluation_data["score"],
        answers=answers,
        evaluation=evaluation_data
    )

    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return new_result

def get_user_results(db: Session, user_id: int):
    return db.query(models.Result)\
        .filter(models.Result.user_id == user_id)\
        .all()