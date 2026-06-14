"""
Question Generator Service
Uses RAG context + resume data to generate targeted interview questions.
"""
import json
import re
from groq import Groq
from config import settings
from services.rag_service import retrieve_context, build_retrieval_query

client = Groq(api_key=settings.GROQ_API_KEY)

# Topic pools per role — used to diversify questions across the session
ROLE_TOPICS = {
    "AI/ML Engineer": [
        "supervised learning", "unsupervised learning", "neural networks",
        "model evaluation", "overfitting & regularization", "feature engineering",
        "NLP fundamentals", "deep learning architecture", "RAG & LLMs",
        "model deployment & MLOps",
    ],
    "Backend Engineer": [
        "REST API design", "database design", "authentication & security",
        "caching strategies", "system scalability", "async processing",
        "containerization", "CI/CD", "data modeling", "error handling",
    ],
    "Data Scientist": [
        "statistical fundamentals", "exploratory data analysis",
        "feature selection", "model selection", "cross-validation",
        "data preprocessing", "visualization", "A/B testing",
        "time series", "business metrics",
    ],
    "Full Stack Engineer": [
        "frontend architecture", "state management", "API integration",
        "database design", "authentication", "performance optimization",
        "testing strategies", "deployment", "security", "system design",
    ],
}

DIFFICULTY_PROGRESSION = ["easy", "medium", "medium", "hard", "hard"]


def _assess_difficulty(skills: list, question_number: int, experience_years: int) -> str:
    """Determine difficulty based on candidate profile + question number."""
    base_idx = min(question_number - 1, len(DIFFICULTY_PROGRESSION) - 1)
    difficulty = DIFFICULTY_PROGRESSION[base_idx]

    if experience_years >= 2 and difficulty == "easy":
        difficulty = "medium"

    return difficulty


def generate_first_question(
    role: str,
    resume_data: dict,
    session_id: str,
) -> dict:
    """Generate the opening question of the interview."""
    return generate_question(
        role=role,
        resume_data=resume_data,
        question_number=1,
        previous_qa=[],
        session_id=session_id,
    )


def generate_question(
    role: str,
    resume_data: dict,
    question_number: int,
    previous_qa: list,
    session_id: str,
) -> dict:
    """
    Core question generation logic.
    1. Pick topic (cycle through role topics, skip covered ones)
    2. Build RAG query from topic + skills
    3. Retrieve context from vector store
    4. Generate question via LLM
    """
    skills = resume_data.get("skills", [])
    technologies = resume_data.get("technologies", [])
    experience_years = resume_data.get("experience", {}).get("years", 0)
    domain_exposure = resume_data.get("domain_exposure", [])

    # Pick topic — rotate through, avoid repeats
    topics = ROLE_TOPICS.get(role, ROLE_TOPICS["AI/ML Engineer"])
    covered_topics = [qa.get("topic", "") for qa in previous_qa]
    available = [t for t in topics if t not in covered_topics]
    topic = available[(question_number - 1) % len(available)] if available else topics[question_number % len(topics)]

    difficulty = _assess_difficulty(skills, question_number, experience_years)

    # RAG retrieval
    rag_query = build_retrieval_query(role, skills + technologies, topic)
    try:
        context = retrieve_context(role, rag_query)
    except Exception:
        context = f"General knowledge about {topic} for {role} role."

    # Build previous QA context for adaptive questioning
    prev_context = ""
    if previous_qa:
        last = previous_qa[-1]
        prev_context = f"""
Previous question: {last.get('question', '')}
Candidate's answer: {last.get('answer', '')}
"""

    prompt = f"""You are a senior technical interviewer conducting a {role} interview.

CANDIDATE PROFILE:
- Skills: {', '.join(skills[:10])}
- Technologies: {', '.join(technologies[:8])}
- Domain: {', '.join(domain_exposure[:5])}
- Experience: {experience_years} years

KNOWLEDGE BASE CONTEXT (use this to ground your question):
{context[:1500]}

TOPIC TO COVER: {topic}
DIFFICULTY: {difficulty}
QUESTION NUMBER: {question_number}
{prev_context}

Generate ONE interview question that:
1. Is grounded in the knowledge base context above
2. Tests {topic} at {difficulty} level
3. Is specific to the candidate's background (not generic)
4. {"Builds on their previous answer" if previous_qa else "Is a good opening question"}
5. Tests conceptual understanding, NOT just definitions

Return ONLY valid JSON:
{{
  "question_text": "Your question here?",
  "rationale": "Why this question for this candidate"
}}

JSON:"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()

    try:
        result = json.loads(raw)
        question_text = result["question_text"]
    except (json.JSONDecodeError, KeyError):
        question_text = raw.strip()

    return {
        "question_text": question_text,
        "topic": topic,
        "difficulty": difficulty,
        "retrieved_context": context[:800],
    }


def evaluate_answer(
    question_text: str,
    answer_text: str,
    topic: str,
    role: str,
    context: str,
) -> dict:
    """Evaluate candidate's answer. Returns {score: 0-10, feedback: str}"""
    prompt = f"""You are evaluating a candidate's answer in a {role} interview.

Topic: {topic}
Question: {question_text}
Candidate's Answer: {answer_text}

Reference context (from knowledge base):
{context[:800]}

Evaluate the answer on:
1. Technical accuracy (0-4 points)
2. Depth of understanding (0-3 points)
3. Clarity and structure (0-3 points)

Return ONLY valid JSON:
{{
  "score": <0-10>,
  "feedback": "Constructive 2-3 sentence feedback highlighting strengths and gaps"
}}

JSON:"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()

    try:
        result = json.loads(raw)
        return {"score": int(result["score"]), "feedback": result["feedback"]}
    except Exception:
        return {"score": 5, "feedback": "Answer recorded. Keep refining your understanding."}


def generate_overall_feedback(role: str, qa_pairs: list, avg_score: float) -> str:
    """Generate final session summary feedback."""
    topics_covered = [qa.get("topic", "") for qa in qa_pairs]

    prompt = f"""You are wrapping up a {role} technical interview.

Topics covered: {', '.join(topics_covered)}
Average score: {avg_score:.1f}/10
Number of questions: {len(qa_pairs)}

Write a 3-4 sentence constructive summary:
- Overall performance assessment
- Strongest area observed
- Key area to improve
- Encouragement

Be specific and professional. Plain text, no JSON needed."""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=250,
    )

    return response.choices[0].message.content.strip()