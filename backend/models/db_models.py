from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=gen_uuid)
    candidate_name = Column(String, nullable=True)
    role = Column(String, nullable=False)
    resume_text = Column(Text, nullable=False)
    extracted_skills = Column(JSON, default=list)
    extracted_experience = Column(JSON, default=dict)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    questions = relationship("Question", back_populates="session", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=gen_uuid)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    retrieved_context = Column(Text, nullable=True)
    topic = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(String, primary_key=True, default=gen_uuid)
    question_id = Column(String, ForeignKey("questions.id"), nullable=False)
    session_id = Column(String, nullable=False)
    answer_text = Column(Text, nullable=False)
    ai_feedback = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    question = relationship("Question", back_populates="answer")