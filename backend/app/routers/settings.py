import os
import shutil
import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import PrivacySetting, Video, Event, AISummary, Notification, RingDevice, AnalysisJob
from ..config import settings
from ..schemas import PrivacySettingResponse, PrivacySettingUpdate
from ..services.video_processor import VideoProcessor

router = APIRouter(prefix="/api/settings", tags=["Settings & Privacy"])

@router.get("")
def get_all_settings(db: Session = Depends(get_db)):
    privacy = db.query(PrivacySetting).first()
    if not privacy:
        privacy = PrivacySetting(retention_days=30, auto_delete=False, blur_faces=False)
        db.add(privacy)
        db.commit()
        db.refresh(privacy)

    return {
        "ai_provider": settings.AI_PROVIDER,
        "gemini_model": settings.GEMINI_MODEL,
        "openai_model": settings.OPENAI_MODEL,
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "has_openai_key": bool(settings.OPENAI_API_KEY),
        "ring_simulator_mode": settings.RING_SIMULATOR_MODE,
        "has_ring_client_id": bool(settings.RING_CLIENT_ID),
        "privacy": PrivacySettingResponse.model_validate(privacy)
    }

@router.post("")
def update_settings(payload: dict = Body(...), db: Session = Depends(get_db)):
    if "ai_provider" in payload:
        settings.AI_PROVIDER = payload["ai_provider"]
    if "gemini_api_key" in payload and payload["gemini_api_key"]:
        settings.GEMINI_API_KEY = payload["gemini_api_key"]
    if "gemini_model" in payload and payload["gemini_model"]:
        settings.GEMINI_MODEL = str(payload["gemini_model"]).strip()
    if "openai_api_key" in payload and payload["openai_api_key"]:
        settings.OPENAI_API_KEY = payload["openai_api_key"]
    if "openai_model" in payload and payload["openai_model"]:
        settings.OPENAI_MODEL = str(payload["openai_model"]).strip()
    if "ring_simulator_mode" in payload:
        settings.RING_SIMULATOR_MODE = bool(payload["ring_simulator_mode"])

    privacy = db.query(PrivacySetting).first()
    if not privacy:
        privacy = PrivacySetting()
        db.add(privacy)

    if "retention_days" in payload:
        privacy.retention_days = int(payload["retention_days"])
    if "auto_delete" in payload:
        privacy.auto_delete = bool(payload["auto_delete"])
    if "blur_faces" in payload:
        privacy.blur_faces = bool(payload["blur_faces"])
    if "local_processing_only" in payload:
        privacy.local_processing_only = bool(payload["local_processing_only"])

    privacy.updated_at = datetime.datetime.utcnow()
    db.commit()

    return {"message": "Settings updated successfully", "status": "success"}

@router.get("/storage-stats")
def get_storage_stats(db: Session = Depends(get_db)):
    # Calculate upload directory size
    upload_bytes = 0
    if os.path.exists(settings.UPLOAD_DIR):
        for root, dirs, files in os.walk(settings.UPLOAD_DIR):
            for f in files:
                upload_bytes += os.path.getsize(os.path.join(root, f))

    frame_bytes = 0
    if os.path.exists(settings.FRAMES_DIR):
        for root, dirs, files in os.walk(settings.FRAMES_DIR):
            for f in files:
                frame_bytes += os.path.getsize(os.path.join(root, f))

    db_bytes = 0
    db_file = "./data/safehome.db"
    if os.path.exists(db_file):
        db_bytes = os.path.getsize(db_file)

    video_count = db.query(Video).count()
    event_count = db.query(Event).count()

    return {
        "upload_size_mb": round(upload_bytes / (1024 * 1024), 2),
        "frames_size_mb": round(frame_bytes / (1024 * 1024), 2),
        "db_size_mb": round(db_bytes / (1024 * 1024), 2),
        "total_storage_mb": round((upload_bytes + frame_bytes + db_bytes) / (1024 * 1024), 2),
        "video_count": video_count,
        "event_count": event_count,
        "storage_location": os.path.abspath(settings.UPLOAD_DIR)
    }

@router.post("/reset-demo-data")
def reset_demo_data(delete_user_files: bool = False, db: Session = Depends(get_db)):
    """
    Cleans any lingering demonstration records from the database while preserving
    all genuine user uploads and real analysis records.
    Never seeds fake data in production.
    """
    db.query(Event).filter(Event.is_demo == True).delete()
    db.query(AISummary).filter(AISummary.is_demo == True).delete()
    db.query(Video).filter(Video.is_demo == True).delete()
    db.query(RingDevice).filter(RingDevice.is_simulator == True).delete()
    db.query(Notification).filter(Notification.notification_type == "test_fixture").delete()

    if delete_user_files:
        user_videos = db.query(Video).filter(Video.is_demo == False).all()
        for v in user_videos:
            if os.path.exists(v.file_path):
                try:
                    os.remove(v.file_path)
                except Exception:
                    pass
            f_dir = os.path.join(settings.FRAMES_DIR, f"vid_{v.id}")
            if os.path.exists(f_dir):
                try:
                    shutil.rmtree(f_dir)
                except Exception:
                    pass
            db.delete(v)

    db.commit()
    return {"message": "Demo data cleaned. Real user records preserved.", "status": "success"}

@router.post("/enforce-retention")
def enforce_retention(db: Session = Depends(get_db)):
    """
    Purges non-demo videos whose retention_expires_at has elapsed or are older
    than the active retention_days policy.
    """
    now = datetime.datetime.utcnow()
    privacy = db.query(PrivacySetting).first()
    retention_days = privacy.retention_days if privacy else 30

    expired_videos = []
    if retention_days > 0:
        cutoff = now - datetime.timedelta(days=retention_days)
        expired_videos = db.query(Video).filter(
            Video.is_demo == False,
            (Video.retention_expires_at <= now) | (Video.created_at <= cutoff)
        ).all()

    purged_count = 0
    for v in expired_videos:
        try:
            if os.path.exists(v.file_path):
                os.remove(v.file_path)
            frame_dir = os.path.join(settings.FRAMES_DIR, f"vid_{v.id}")
            if os.path.exists(frame_dir):
                shutil.rmtree(frame_dir)
        except Exception as e:
            print(f"Error purging video files: {e}")
        db.delete(v)
        purged_count += 1

    db.commit()
    return {
        "status": "success",
        "purged_count": purged_count,
        "message": f"Purged {purged_count} expired video file(s) per retention policy ({retention_days} days)."
    }

