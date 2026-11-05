import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings(BaseModel):
    PROJECT_NAME: str = "Voyantra API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Host
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # Supabase / Database Settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./voyantra.db")
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "voyantra_db")
    
    # AI / LLM (Google Gemini API Free Tier)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "voyantra_jwt_secret_key_prod_2026_pondicherry_chennai")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    # Comma-separated list, e.g. CORS_ORIGINS="https://app.example.com,https://www.example.com"
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"
        ).split(",") if o.strip()
    ]

    # Set true only when running behind a trusted reverse proxy (uses X-Forwarded-For for rate limiting)
    TRUST_PROXY_HEADERS: bool = os.getenv("TRUST_PROXY_HEADERS", "False").lower() == "true"
    
    # OSRM Routing Engines
    OSRM_LOCAL_DRIVING_URL: str = os.getenv("OSRM_LOCAL_DRIVING_URL", "http://localhost:5000")
    OSRM_LOCAL_WALKING_URL: str = os.getenv("OSRM_LOCAL_WALKING_URL", "http://localhost:5001")
    OSRM_PUBLIC_DEMO_URL: str = os.getenv("OSRM_PUBLIC_DEMO_URL", "http://router.project-osrm.org")
    OSRM_TIMEOUT_SECONDS: float = float(os.getenv("OSRM_TIMEOUT_SECONDS", "3.0"))

    # Knowledge Engine (VTKE)
    KNOWLEDGE_RAG_ENABLED: bool = os.getenv("KNOWLEDGE_RAG_ENABLED", "True").lower() == "true"
    KNOWLEDGE_GEMINI_EMBEDDING_MODEL: str = os.getenv("KNOWLEDGE_GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
    KNOWLEDGE_VECTOR_INDEX_DIR: str = os.getenv(
        "KNOWLEDGE_VECTOR_INDEX_DIR",
        str(Path(__file__).resolve().parent.parent / "data" / "knowledge_vectors")
    )
    KNOWLEDGE_CRAWL_ALLOWED_DOMAINS: list[str] = [
        "voyantra.com",
        "localhost",
        "127.0.0.1"
    ]
    KNOWLEDGE_MAX_REDIRECT_HOPS: int = 3
    KNOWLEDGE_WORKER_LEASE_SECONDS: int = 120
    KNOWLEDGE_WORKER_HEARTBEAT_SECONDS: int = 30
    KNOWLEDGE_WORKER_MAX_RETRIES: int = 3

settings = Settings()
