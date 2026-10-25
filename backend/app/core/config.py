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
    
    # AI / LLM (Google Gemini API Free Tier)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # JWT Settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "voyantra_jwt_secret_key_prod_2026_pondicherry_chennai")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]
    
    # OSRM Routing Engines
    OSRM_LOCAL_DRIVING_URL: str = os.getenv("OSRM_LOCAL_DRIVING_URL", "http://localhost:5000")
    OSRM_LOCAL_WALKING_URL: str = os.getenv("OSRM_LOCAL_WALKING_URL", "http://localhost:5001")
    OSRM_PUBLIC_DEMO_URL: str = os.getenv("OSRM_PUBLIC_DEMO_URL", "http://router.project-osrm.org")
    OSRM_TIMEOUT_SECONDS: float = float(os.getenv("OSRM_TIMEOUT_SECONDS", "3.0"))

settings = Settings()
