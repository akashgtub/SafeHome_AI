import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    DATABASE_URL: str = "sqlite:///./data/safehome.db"

    UPLOAD_DIR: str = "./data/uploads"
    FRAMES_DIR: str = "./data/frames"
    SAMPLE_DIR: str = "./data/sample"

    MAX_UPLOAD_SIZE_MB: int = 200
    MAX_VIDEO_DURATION_SECONDS: int = 600

    AI_PROVIDER: str = "mock"  # "mock", "gemini", "openai"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    RING_CLIENT_ID: str = ""
    RING_CLIENT_SECRET: str = ""
    RING_REDIRECT_URI: str = "http://localhost:8000/api/ring/oauth/callback"
    RING_WEBHOOK_SECRET: str = ""
    RING_SIMULATOR_MODE: bool = True

    DEFAULT_RETENTION_DAYS: int = 30
    AUTO_DELETE_EXPIRED: bool = False
    BLUR_FACES_DEFAULT: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

# Ensure directories exist
for path in [settings.UPLOAD_DIR, settings.FRAMES_DIR, settings.SAMPLE_DIR, "./data"]:
    os.makedirs(path, exist_ok=True)
