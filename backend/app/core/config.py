from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "SentinelX SOC Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "sentinelx_soc_super_secret_jwt_signing_key_for_btech_major_project_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sentinelx.db")
    SYNC_DATABASE_URL: str = os.getenv("SYNC_DATABASE_URL", "sqlite:///./sentinelx.db")
    
    # File Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./data/uploads")
    SAMPLES_DIR: str = os.getenv("SAMPLES_DIR", "./data/samples")
    INTEL_DIR: str = os.getenv("INTEL_DIR", "./data/intel")
    MODELS_DIR: str = os.getenv("MODELS_DIR", "./ml/models")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:3000"]
    
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

settings = Settings()
