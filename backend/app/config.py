import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"

    DATABASE_URL: str = "sqlite:///./data/safehome.db"

    UPLOAD_DIR: str = "./data/uploads"
    FRAMES_DIR: str = "./data/frames"
    SAMPLE_DIR: str = "./data/sample"

    MAX_UPLOAD_SIZE_MB: int = 200
    MAX_VIDEO_DURATION_SECONDS: int = 600

    AI_PROVIDER: str = "gemini"  # "gemini", "openai", "local"
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

    # Motion Deduplication & Analysis Tolerances
    MOTION_GROUPING_TOLERANCE_SECONDS: float = 2.0
    MIN_MOTION_DURATION_SECONDS: float = 1.0
    DEMO_MODE_ENABLED: bool = False

    class Config:
        env_file = (
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
            ".env"
        )
        extra = "ignore"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()

# Ensure directories exist
for path in [settings.UPLOAD_DIR, settings.FRAMES_DIR, settings.SAMPLE_DIR, "./data"]:
    os.makedirs(path, exist_ok=True)
