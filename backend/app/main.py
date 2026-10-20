import os
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .database import init_db, SessionLocal
from .models import Video, AnalysisJob, Event, AISummary, RingDevice, PrivacySetting, Notification
from .services.video_processor import VideoProcessor
from .routers import dashboard, videos, events, summaries, ring, notifications, settings as settings_router

app = FastAPI(
    title="SafeHome AI — Smart Home Safety Platform",
    description="Backend API for AI-powered video security analysis, Amazon Ring integration, and evidence-grounded summarization.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(dashboard.router)
app.include_router(videos.router)
app.include_router(events.router)
app.include_router(summaries.router)
app.include_router(ring.router)
app.include_router(notifications.router)
app.include_router(settings_router.router)

# Mount static directories
app.mount("/data/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/data/frames", StaticFiles(directory=settings.FRAMES_DIR), name="frames")
app.mount("/data/sample", StaticFiles(directory=settings.SAMPLE_DIR), name="sample")

def seed_demo_data(db=None):
    """
    Disabled for Production: SafeHome AI exclusively processes genuine user recordings
    and live Ring events. No fake videos, events, or notifications are generated.
    """
    pass

@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        # Initialize baseline privacy settings if not existing
        if not db.query(PrivacySetting).first():
            privacy = PrivacySetting(retention_days=30, auto_delete=False, blur_faces=False)
            db.add(privacy)
            db.commit()
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": "SafeHome AI",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to SafeHome AI API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", settings.PORT))
    app_entry = "backend.app.main:app" if os.path.exists("backend") else "app.main:app"
    uvicorn.run(app_entry, host=settings.HOST, port=port, reload=False)

