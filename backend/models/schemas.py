from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


# ── Session ──────────────────────────────────────────────
class SessionCreate(BaseModel):
    role: str
    candidate_name: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    candidate_name: Optional[str]
    role: str
    status: str
    extracted_skills: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Resume ───────────────────────────────────────────────
class ResumeParseResult(BaseModel):
    raw_text: str
    skills: List[str]
    experience: Dict[str, Any]
    technologies: List[str]
    domain_exposure: List[str]


# ── Question ─────────────────────────────────────────────
class QuestionResponse(BaseModel):
    id: str
    question_number: int
    question_text: str
    topic: Optional[str]
    difficulty: Optional[str]

    class Config:
        from_attributes = True


# ── Answer ───────────────────────────────────────────────
class AnswerSubmit(BaseModel):
    session_id: str
    question_id: str
    answer_text: str


class AnswerResponse(BaseModel):
    id: str
    answer_text: str
    ai_feedback: Optional[str]
    score: Optional[int]
    next_question: Optional[QuestionResponse] = None

    class Config:
        from_attributes = True


# ── Summary ──────────────────────────────────────────────
class QuestionAnswerPair(BaseModel):
    question_number: int
    question_text: str
    topic: Optional[str]
    difficulty: Optional[str]
    answer_text: str
    ai_feedback: Optional[str]
    score: Optional[int]


class SessionSummary(BaseModel):
    session_id: str
    candidate_name: Optional[str]
    role: str
    skills_evaluated: List[str]
    total_questions: int
    average_score: Optional[float]
    qa_pairs: List[QuestionAnswerPair]
    overall_feedback: str
    created_at: datetime
    completed_at: Optional[datetime]


# ── Ingest ───────────────────────────────────────────────
class IngestResponse(BaseModel):
    role: str
    chunks_indexed: int
    message: str