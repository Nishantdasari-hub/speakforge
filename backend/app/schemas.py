from pydantic import BaseModel, EmailStr
from typing import List
from typing import Optional
from datetime import datetime


# ================== USER ==================

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


# ================== QUESTION ==================

class QuestionCreate(BaseModel):
    question_text: str
    question_type: str
    time_limit: int
    order_number: int


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    question_type: Optional[str] = None
    time_limit: Optional[int] = None
    order_number: Optional[int] = None

    class Config:
        from_attributes = True

# ================== TEST ==================

class TestCreate(BaseModel):
    title: str
    description: str


class TestResponse(BaseModel):
    id: int
    title: str
    description: str
    created_at: datetime
    questions: List[QuestionResponse] = []

    model_config = {
        "from_attributes": True
    }

class AnswerSubmission(BaseModel):
    question_id: int
    written_answer: Optional[str] = None
    audio_path: Optional[str] = None

class QuestionAnswerResponse(BaseModel):
    id: int
    user_id: int
    question_id: int
    written_answer: Optional[str] = None
    audio_path: Optional[str] = None
    transcribed_text: Optional[str] = None
    grammar_score: Optional[int] = None
    fluency_score: Optional[float] = None
    final_score: Optional[int] = None
    grammar_errors: Optional[int] = None
    word_count: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class SubmitTest(BaseModel):
    answers: List[AnswerSubmission]
    
class ResultResponse(BaseModel):
    id: int
    user_id: int
    test_id: int
    score: float
    answers: Optional[list] = None
    evaluation: Optional[dict] = None
    submitted_at: datetime

    class Config:
        from_attributes = True

class TextAnswer(BaseModel):
    answer: str

class UserResultResponse(BaseModel):
    id: int
    score: float
    evaluation:Optional[dict] = None
    submitted_at: datetime
    test_id: int

    model_config = {
        "from_attributes": True
    }

