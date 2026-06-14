"""
Session Manager Service
Handles session lifecycle: create, get, update, complete.
"""
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from models.db_models import Session, Question, Answer
from models.schemas import SessionSummary, QuestionAnswerPair


def create_session(
    db: DBSession,
    role: str,
    resume_data: dict,
    candidate_name: str = None,
) -> Session:
    session = Session(
        role=role,
        candidate_name=candidate_name,
        resume_text=resume_data.get("raw_text", ""),
        extracted_skills=resume_data.get("skills", []),
        extracted_experience=resume_data.get("experience", {}),
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: DBSession, session_id: str) -> Session:
    return db.query(Session).filter(Session.id == session_id).first()


def save_question(
    db: DBSession,
    session_id: str,
    question_number: int,
    question_data: dict,
) -> Question:
    question = Question(
        session_id=session_id,
        question_number=question_number,
        question_text=question_data["question_text"],
        retrieved_context=question_data.get("retrieved_context", ""),
        topic=question_data.get("topic", ""),
        difficulty=question_data.get("difficulty", "medium"),
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def save_answer(
    db: DBSession,
    question_id: str,
    session_id: str,
    answer_text: str,
    score: int = None,
    feedback: str = None,
) -> Answer:
    answer = Answer(
        question_id=question_id,
        session_id=session_id,
        answer_text=answer_text,
        score=score,
        ai_feedback=feedback,
    )
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def get_session_qa_history(db: DBSession, session_id: str) -> list:
    """Return list of {question, answer} dicts for adaptive questioning."""
    questions = (
        db.query(Question)
        .filter(Question.session_id == session_id)
        .order_by(Question.question_number)
        .all()
    )

    history = []
    for q in questions:
        if q.answer:
            history.append({
                "question": q.question_text,
                "answer": q.answer.answer_text,
                "topic": q.topic,
            })
    return history


def get_question_count(db: DBSession, session_id: str) -> int:
    return db.query(Question).filter(Question.session_id == session_id).count()


def complete_session(db: DBSession, session_id: str) -> Session:
    session = get_session(db, session_id)
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    return session


def build_session_summary(
    db: DBSession,
    session_id: str,
    overall_feedback: str,
) -> SessionSummary:
    session = get_session(db, session_id)
    questions = (
        db.query(Question)
        .filter(Question.session_id == session_id)
        .order_by(Question.question_number)
        .all()
    )

    qa_pairs = []
    scores = []
    for q in questions:
        ans = q.answer
        if ans:
            qa_pairs.append(QuestionAnswerPair(
                question_number=q.question_number,
                question_text=q.question_text,
                topic=q.topic,
                difficulty=q.difficulty,
                answer_text=ans.answer_text,
                ai_feedback=ans.ai_feedback,
                score=ans.score,
            ))
            if ans.score is not None:
                scores.append(ans.score)

    avg_score = sum(scores) / len(scores) if scores else None

    return SessionSummary(
        session_id=session_id,
        candidate_name=session.candidate_name,
        role=session.role,
        skills_evaluated=session.extracted_skills or [],
        total_questions=len(qa_pairs),
        average_score=avg_score,
        qa_pairs=qa_pairs,
        overall_feedback=overall_feedback,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )