import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./documind.db")
    # For sync operations if needed (like Alembic)
    SYNC_DATABASE_URL: str = os.getenv("SYNC_DATABASE_URL", "sqlite:///./documind.db")
    
    # Security & Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "documind-super-secret-production-key-change-in-prod-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Storage Paths
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage/pdfs")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./storage/chromadb")
    
    # AI & ML Models
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    CROSS_ENCODER_MODEL_NAME: str = os.getenv("CROSS_ENCODER_MODEL_NAME", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    ENABLE_CROSS_ENCODER: bool = os.getenv("ENABLE_CROSS_ENCODER", "False").lower() in ("true", "1", "yes")
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")  # 'gemini', 'openai', 'local', or 'auto'
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    
    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000"
        ).split(",")
        if origin.strip()
    ]
    
    # Document Processing & Chunking
    DEFAULT_CHUNK_SIZE: int = 600
    DEFAULT_CHUNK_OVERLAP: int = 100
    MAX_FILE_SIZE_MB: int = 50
    
    # Retrieval Configuration
    BM25_K1: float = 1.5
    BM25_B: float = 0.75
    RRF_K: int = 60
    TOP_K_RETRIEVAL: int = 6
    EVIDENCE_CONFIDENCE_THRESHOLD: float = 0.35

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow"
    }


settings = Settings()
