from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean,Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from sqlalchemy import JSON


# -------------------- USER --------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    answers = relationship("QuestionAnswer", back_populates="user")
    reset_token = Column(String(255), nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)


# -------------------- TEST --------------------

class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="test")


# -------------------- QUESTION --------------------

# -------------------- QUESTION --------------------

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    question_text = Column(Text)
    question_type = Column(String(20))   # text OR audio
    time_limit = Column(Integer)
    order_number = Column(Integer)

    test = relationship("Test", back_populates="questions")
    answers = relationship("QuestionAnswer", back_populates="question")
# -------------------- QUESTION ANSWER --------------------

class QuestionAnswer(Base):
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))

    written_answer = Column(Text, nullable=True)  # For text-based answers
    audio_path = Column(String(255), nullable=True)  # For audio files
    transcribed_text = Column(Text, nullable=True)  # For transcribed audio text
    
    # Evaluation fields
    grammar_score = Column(Integer, nullable=True)
    fluency_score = Column(Float, nullable=True)
    final_score = Column(Integer, nullable=True)
    grammar_errors = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)  # Track word count for analytics
    feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    test_id = Column(Integer, ForeignKey("tests.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

# -------------------- RESULT --------------------

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    test_id = Column(Integer, ForeignKey("tests.id"))

    score = Column(Float)

    answers = Column(JSON)        # stores answers list
    evaluation = Column(JSON)     # stores AI evaluation report

    submitted_at = Column(DateTime, default=datetime.utcnow)