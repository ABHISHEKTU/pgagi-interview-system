"""
Sessions Router
POST /api/sessions/start  — upload resume + select role → create session
GET  /api/sessions/{id}   — get session details
GET  /api/sessions/{id}/summary — get final summary
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session as DBSession
from database import get_db
from services.resume_parser import parse_resume
from services.session_manager import (
    create_session, get_session, complete_session, build_session_summary
)
from services.question_generator import generate_first_question, generate_overall_feedback
from services.session_manager import save_question, get_question_count

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

VALID_ROLES = ["AI/ML Engineer", "Backend Engineer", "Data Scientist", "Full Stack Engineer"]
MAX_QUESTIONS = 5


@router.post("/start")
async def start_session(
    resume: UploadFile = File(...),
    role: str = Form(...),
    candidate_name: str = Form(None),
    db: DBSession = Depends(get_db),
):
    if role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose from: {VALID_ROLES}")

    if not (resume.filename.endswith(".pdf") or resume.filename.endswith(".txt")):
        raise HTTPException(status_code=400, detail="Only PDF or TXT resumes accepted.")

    try:
        file_bytes = await resume.read()
        resume_data = parse_resume(file_bytes, resume.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Resume parsing failed: {str(e)}")

    session = create_session(db, role, resume_data, candidate_name)

    try:
        q_data = generate_first_question(role, resume_data, session.id)
        question = save_question(db, session.id, 1, q_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

    return {
        "session_id": session.id,
        "candidate_name": session.candidate_name,
        "role": role,
        "extracted_skills": resume_data.get("skills", []),
        "extracted_technologies": resume_data.get("technologies", []),
        "domain_exposure": resume_data.get("domain_exposure", []),
        "total_questions": MAX_QUESTIONS,
        "first_question": {
            "id": question.id,
            "question_number": 1,
            "question_text": question.question_text,
            "topic": question.topic,
            "difficulty": question.difficulty,
        },
    }


@router.get("/{session_id}")
async def get_session_details(session_id: str, db: DBSession = Depends(get_db)):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    return {
        "session_id": session.id,
        "candidate_name": session.candidate_name,
        "role": session.role,
        "status": session.status,
        "extracted_skills": session.extracted_skills,
        "questions_answered": get_question_count(db, session_id),
        "total_questions": MAX_QUESTIONS,
        "created_at": session.created_at,
    }


@router.get("/{session_id}/summary")
async def get_session_summary(session_id: str, db: DBSession = Depends(get_db)):
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Interview not yet completed.")

    from models.db_models import Question
    questions = db.query(Question).filter(Question.session_id == session_id).all()
    qa_pairs_raw = [
        {"question": q.question_text, "answer": q.answer.answer_text if q.answer else "", "topic": q.topic}
        for q in questions if q.answer
    ]

    scores = [q.answer.score for q in questions if q.answer and q.answer.score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0

    overall_feedback = generate_overall_feedback(session.role, qa_pairs_raw, avg_score)
    complete_session(db, session_id)

    return build_session_summary(db, session_id, overall_feedback)