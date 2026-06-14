from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Groq
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama3-70b-8192"

    # Database
    DATABASE_URL: str

    # App
    APP_ENV: str = "development"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # RAG
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_PATH: str = "./vector_store"
    KNOWLEDGE_BASE_PATH: str = "./knowledge_base"
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_RETRIEVAL: int = 5

    class Config:
        env_file = ".env"


settings = Settings()