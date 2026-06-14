# PGAGI AI Interview System

An AI-powered, role-based candidate screening system that conducts dynamic technical interviews using RAG (Retrieval-Augmented Generation).

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![React](https://img.shields.io/badge/React-18-61dafb)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791)
![FAISS](https://img.shields.io/badge/FAISS-Vector_DB-orange)
![Groq](https://img.shields.io/badge/Groq-Llama3-purple)

## Demo Video
[Watch Demo →](https://drive.google.com/file/d/11CAMAbAbxSVYpsfrTKwc8NsJL1admeiG/view?usp=drive_link)

---

## What It Does

Instead of using fixed interview questions, this system:
1. Parses your resume using an LLM to extract skills, technologies, and domain exposure
2. Retrieves relevant content from ML textbooks using RAG (FAISS + sentence-transformers)
3. Dynamically generates interview questions grounded in the knowledge base
4. Evaluates your answers with AI feedback and a score (0–10)
5. Adapts follow-up questions based on your previous answers
6. Generates a full structured summary at the end

---

## System Architecture

┌─────────────────────────────────────────────────────────┐

│                 React Frontend (Vite)                    │

│     Upload Page → Interview Page → Summary Page         │

└───────────────────────┬─────────────────────────────────┘

│ REST API

┌───────────────────────▼─────────────────────────────────┐

│                   FastAPI Backend                        │

│                                                         │

│  /api/sessions/start   → Resume Parse + Q1 Gen          │

│  /api/interview/answer → Evaluate + Next Q Gen          │

│  /api/sessions/summary → Final Report                   │

│  /api/ingest           → Vector Store Build             │

└──────┬────────────────┬────────────────┬────────────────┘

│                │                │

┌──────▼──────┐  ┌──────▼──────┐  ┌─────▼──────────────┐

│  PostgreSQL  │  │    FAISS    │  │   Groq (Llama3)    │

│  Sessions   │  │  Vector DB  │  │  LLM Inference     │

│  Questions  │  │  per Role   │  │  Q-Gen + Eval      │

│  Answers    │  │             │  │                    │

└─────────────┘  └─────────────┘  └────────────────────┘

## RAG Pipeline

PDF Books (per role)

↓ PyMuPDF text extraction

↓ RecursiveCharacterTextSplitter (800 tokens, 150 overlap)

↓ HuggingFace Embeddings (all-MiniLM-L6-v2)

↓ FAISS Index (saved per role)
Interview Flow:

Resume Skills + Role + Topic

↓ Dynamic query construction

↓ FAISS similarity search (top-5 chunks)

↓ Retrieved context → Groq LLM (Llama3)

↓ Grounded question generation

↓ Answer evaluation + scoring (0–10)

↓ Adaptive next question (uses previous Q&A history)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite |
| Backend | FastAPI, Python 3.10+ |
| Database | PostgreSQL |
| Vector Store | FAISS |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Groq API (Llama3-70b) |
| PDF Parsing | PyMuPDF |
| ORM | SQLAlchemy |

---

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Embeddings | all-MiniLM-L6-v2 | Fast, local, no API cost |
| LLM | Groq Llama3 | Fast inference, strong reasoning |
| Vector DB | FAISS | Simple, file-based, no extra service |
| Chunking | 800 tok / 150 overlap | Preserves context across boundaries |
| Retrieval | Top-5 chunks | Enough context without exceeding LLM window |
| DB | PostgreSQL | Full traceability: session → question → answer |
| Questions | 5 per session | Enough depth without fatigue |

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL

### 1. Clone the repo
```bash
git clone https://github.com/ABHISHEKTU/pgagi-interview-system.git
cd pgagi-interview-system
```

### 2. Backend Setup
```bash
cd backend
cp .env.example .env
# Fill in GROQ_API_KEY and DATABASE_URL in .env

pip install -r requirements.txt
```

### 3. Create PostgreSQL Database
```bash
psql -U postgres
CREATE DATABASE pgagi_interview;
\q
```

### 4. Add Knowledge Base

backend/knowledge_base/

└── aiml/

├── mitchell_ml.pdf

└── hundred_page_ml.pdf

### 5. Start Backend
```bash
cd backend
uvicorn main:app --reload
```

### 6. Index Knowledge Base (one-time)
```bash
curl -X POST http://localhost:8000/api/ingest/ \
  -H "Content-Type: application/json" \
  -d '{"role": "AI/ML Engineer"}'
```

### 7. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions/start` | Upload resume + start interview |
| GET | `/api/sessions/{id}` | Get session status |
| POST | `/api/interview/answer` | Submit answer, get next question |
| GET | `/api/sessions/{id}/summary` | Get final report |
| POST | `/api/ingest/` | Index PDFs for a role |
| GET | `/api/ingest/status` | Check which roles are indexed |

---

## Project Structure

pgagi-interview-system/

├── backend/

│   ├── main.py

│   ├── config.py

│   ├── database.py

│   ├── routers/

│   │   ├── sessions.py

│   │   ├── interview.py

│   │   └── ingest.py

│   ├── services/

│   │   ├── rag_service.py

│   │   ├── resume_parser.py

│   │   ├── question_generator.py

│   │   └── session_manager.py

│   └── models/

│       ├── db_models.py

│       └── schemas.py

└── frontend/

└── src/

├── App.jsx

├── pages/

│   ├── UploadPage.jsx

│   ├── InterviewPage.jsx

│   └── SummaryPage.jsx

└── services/

└── api.js

---

## Author

**Abhishek T U**
- GitHub: [@ABHISHEKTU](https://github.com/ABHISHEKTU)
- LinkedIn: [linkedin.com/in/abhishek-t-u](https://linkedin.com/in/abhishek-t-u)

