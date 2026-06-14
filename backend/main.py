from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import init_db
from routers import sessions, interview, ingest


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("✅ Database initialized")
    yield


app = FastAPI(
    title="PGAGI Interview System",
    description="AI-powered role-based candidate screening system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(interview.router)
app.include_router(ingest.router)


@app.get("/")
async def root():
    return {
        "message": "PGAGI Interview System API",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}