"""
Resume Parser Service
Extracts skills, technologies, experience, and domain exposure from resume text.
Uses Groq/LLM for intelligent extraction.
"""
import fitz  # PyMuPDF
import json
import re
from groq import Groq
from config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

KNOWN_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust",
    "FastAPI", "Django", "Flask", "Node.js", "Express", "Next.js", "React",
    "PyTorch", "TensorFlow", "Keras", "Scikit-learn", "NumPy", "Pandas",
    "LangChain", "FAISS", "Hugging Face", "OpenAI", "LlamaIndex",
    "PostgreSQL", "MongoDB", "MySQL", "Redis", "SQLite",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "Git", "GitHub", "CI/CD", "REST API", "GraphQL",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "RAG",
    "Transformer", "BERT", "GPT", "CNN", "RNN", "LSTM",
]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract raw text from PDF bytes using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()


def extract_skills_regex(text: str) -> list[str]:
    """Fast regex-based skill extraction as baseline."""
    found = []
    text_lower = text.lower()
    for skill in KNOWN_SKILLS:
        if skill.lower() in text_lower:
            found.append(skill)
    return list(set(found))


def parse_resume_with_llm(resume_text: str) -> dict:
    """
    Use Groq LLM to intelligently extract structured info from resume.
    Returns dict with skills, experience, technologies, domain_exposure.
    """
    prompt = f"""You are a resume parser. Extract structured information from the resume below.

Return ONLY valid JSON with this exact structure:
{{
  "skills": ["skill1", "skill2"],
  "technologies": ["tech1", "tech2"],
  "domain_exposure": ["domain1", "domain2"],
  "experience": {{
    "years": 0,
    "roles": ["role1"],
    "highlights": ["achievement1"]
  }},
  "education": {{
    "degree": "degree name",
    "field": "field of study",
    "institution": "institution name"
  }}
}}

Rules:
- skills: technical + soft skills
- technologies: specific tools, frameworks, libraries
- domain_exposure: problem domains (e.g. "Computer Vision", "NLP", "Web Development")
- experience.years: total years of experience (0 if fresher/student)
- Be specific, not generic

RESUME:
{resume_text[:3000]}

JSON:"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json\s*|\s*```", "", raw).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "skills": extract_skills_regex(resume_text),
            "technologies": extract_skills_regex(resume_text),
            "domain_exposure": [],
            "experience": {"years": 0, "roles": [], "highlights": []},
            "education": {"degree": "", "field": "", "institution": ""},
        }

    return parsed


def parse_resume(file_bytes: bytes, filename: str) -> dict:
    """
    Main entry point. Accepts PDF bytes or text.
    Returns full parsed resume dict + raw text.
    """
    if filename.lower().endswith(".pdf"):
        raw_text = extract_text_from_pdf(file_bytes)
    else:
        raw_text = file_bytes.decode("utf-8", errors="ignore")

    parsed = parse_resume_with_llm(raw_text)
    parsed["raw_text"] = raw_text

    return parsed