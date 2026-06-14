"""
Interview Router
POST /api/interview/answer  — submit answer, get feedback + next question
POST /api/interview/complete — force complete session
GET  /api/interview/{session_id}/questions — get all questions
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from database import get_db
from models.db_models import Question, Answer
from services.session_manager import (
    get_session, save_answer, save_question,
    get_session_qa_history, get_question_count, complete_session
)
from services.question_generator import generate_question, evaluate_answer

router = APIRouter(prefix="/api/interview", tags=["interview"])

MAX_QUESTIONS = 5


class AnswerSubmit(BaseModel):
    session_id: str
    question_id: str
    answer_text: str


@router.post("/answer")
async def submit_answer(payload: AnswerSubmit, db: DBSession = Depends(get_db)):
    session = get_session(db, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="Interview already completed.")

    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")
    if question.answer:
        raise HTTPException(status_code=400, detail="Question already answered.")

    eval_result = evaluate_answer(
        question_text=question.question_text,
        answer_text=payload.answer_text,
        topic=question.topic or "",
        role=session.role,
        context=question.retrieved_context or "",
    )

    answer = save_answer(
        db=db,
        question_id=payload.question_id,
        session_id=payload.session_id,
        answer_text=payload.answer_text,
        score=eval_result["score"],
        feedback=eval_result["feedback"],
    )

    answered_count = get_question_count(db, payload.session_id)
    is_last = answered_count >= MAX_QUESTIONS

    next_question = None
    if not is_last:
        history = get_session_qa_history(db, payload.session_id)

        resume_data = {
            "skills": session.extracted_skills or [],
            "technologies": [],
            "experience": session.extracted_experience or {},
            "domain_exposure": [],
        }

        q_data = generate_question(
            role=session.role,
            resume_data=resume_data,
            question_number=answered_count + 1,
            previous_qa=history,
            session_id=payload.session_id,
        )
        next_q = save_question(db, payload.session_id, answered_count + 1, q_data)
        next_question = {
            "id": next_q.id,
            "question_number": next_q.question_number,
            "question_text": next_q.question_text,
            "topic": next_q.topic,
            "difficulty": next_q.difficulty,
        }
    else:
        complete_session(db, payload.session_id)

    return {
        "answer_id": answer.id,
        "score": eval_result["score"],
        "feedback": eval_result["feedback"],
        "question_number": question.question_number,
        "is_last_question": is_last,
        "next_question": next_question,
    }


@router.post("/complete/{session_id}")
async def force_complete(session_id: str, db: DBSession = Depends(get_db)):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    complete_session(db, session_id)
    return {"message": "Session marked as completed.", "session_id": session_id}


@router.get("/{session_id}/questions")
async def get_all_questions(session_id: str, db: DBSession = Depends(get_db)):
    questions = (
        db.query(Question)
        .filter(Question.session_id == session_id)
        .order_by(Question.question_number)
        .all()
    )
    return [
        {
            "id": q.id,
            "question_number": q.question_number,
            "question_text": q.question_text,
            "topic": q.topic,
            "difficulty": q.difficulty,
            "has_answer": q.answer is not None,
        }
        for q in questions
    ]