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

def seed_demo_data(db):
    """
    Ensures initial database has genuine demonstration video and baseline records
    matching the target UI design.
    """
    demo_video_path = os.path.join(settings.SAMPLE_DIR, "front_door_recording.mp4")
    
    # 1. Generate playable demo video if absent
    if not os.path.exists(demo_video_path):
        print("[SafeHome AI] Generating demo security camera clip...")
        VideoProcessor.generate_demo_video(demo_video_path, duration_sec=20)

    # 2. Check if demo video is registered in DB
    demo_video = db.query(Video).filter(Video.filename == "front_door_recording.mp4").first()
    if not demo_video:
        file_size = os.path.getsize(demo_video_path) if os.path.exists(demo_video_path) else 1024000
        demo_video = Video(
            filename="front_door_recording.mp4",
            original_filename="front_door_recording.mp4",
            file_path=demo_video_path,
            file_size=file_size,
            duration=20.0,
            width=720,
            height=480,
            fps=20.0,
            status="completed",
            is_demo=True,
            created_at=datetime.datetime(2026, 10, 18, 16, 32, 15)
        )
        db.add(demo_video)
        db.commit()
        db.refresh(demo_video)

        # Sample frames for demo video
        sampled = VideoProcessor.sample_frames_and_detect_motion(
            video_id=demo_video.id,
            file_path=demo_video.file_path,
            sample_interval_sec=1.0
        )

        # Analysis job
        job = AnalysisJob(
            video_id=demo_video.id,
            status="completed",
            progress=100,
            frames_analyzed=len(sampled) or 60,
            model_used="Vision AI (Local)",
            created_at=datetime.datetime(2026, 10, 18, 16, 32, 20),
            completed_at=datetime.datetime(2026, 10, 18, 16, 35, 0)
        )
        db.add(job)

        # Seed the 3 verified detected events from the UI
        e1 = Event(
            video_id=demo_video.id,
            source="uploaded_video",
            category="Person",
            title="Person detected",
            description="A person appears near the front entrance.",
            start_time="00:04",
            end_time="00:11",
            start_seconds=4.0,
            end_seconds=11.0,
            timestamp=datetime.datetime(2026, 10, 18, 16, 32, 19),
            priority="Medium",
            priority_reason="Activity was observed near the entrance. This is not a confirmed threat.",
            review_status="Pending Review",
            location="Front Door",
            confidence=0.95,
            thumbnail_path=sampled[4]["frame_url"] if len(sampled) > 4 else None,
            raw_evidence="Pedestrian in dark jacket and backpack approached porch steps, paused facing entrance, then turned back.",
            is_demo=True
        )
        e2 = Event(
            video_id=demo_video.id,
            source="uploaded_video",
            category="Vehicle",
            title="Vehicle detected",
            description="A vehicle passes by on the street.",
            start_time="00:12",
            end_time="00:16",
            start_seconds=12.0,
            end_seconds=16.0,
            timestamp=datetime.datetime(2026, 10, 18, 16, 32, 27),
            priority="Low",
            priority_reason="Standard street transit outside immediate property boundary.",
            review_status="Pending Review",
            location="Street View",
            confidence=0.91,
            thumbnail_path=sampled[12]["frame_url"] if len(sampled) > 12 else None,
            raw_evidence="Passing vehicle traveling along background road.",
            is_demo=True
        )
        e3 = Event(
            video_id=demo_video.id,
            source="uploaded_video",
            category="Motion",
            title="No significant activity",
            description="No notable movement detected.",
            start_time="00:17",
            end_time="00:20",
            start_seconds=17.0,
            end_seconds=20.0,
            timestamp=datetime.datetime(2026, 10, 18, 16, 32, 35),
            priority="Low",
            priority_reason="Normal quiescent background monitoring.",
            review_status="Reviewed",
            location="Front Door",
            confidence=0.99,
            thumbnail_path=sampled[17]["frame_url"] if len(sampled) > 17 else None,
            raw_evidence="Background subtractor delta remained below minimal threshold.",
            is_demo=True
        )
        db.add_all([e1, e2, e3])
        db.commit()

        # Seed additional historical events so dashboard has total 28 events
        event_types = [
            ("Person", "Visitor at front porch", "Low", "00:02", "00:08", "Pending Review"),
            ("Package", "Package placed at doorstep", "Low", "00:03", "00:07", "Pending Review"),
            ("Vehicle", "Delivery van in driveway", "Low", "00:01", "00:14", "Reviewed"),
            ("Motion", "Backyard motion triggered", "Low", "00:05", "00:09", "Reviewed"),
            ("Person", "Approach detected near walkway", "Medium", "00:02", "00:10", "Pending Review"),
            ("Person", "Doorbell button pressed", "Medium", "00:01", "00:06", "Reviewed"),
        ]
        for i in range(25):
            t = event_types[i % len(event_types)]
            past_time = datetime.datetime.utcnow() - datetime.timedelta(hours=i*5 + 2)
            db.add(Event(
                source="ring_integration" if i % 2 == 0 else "simulator",
                category=t[0],
                title=f"{t[1]} #{i+4}",
                description=f"Automated security detection logged at {t[3]}.",
                start_time=t[3],
                end_time=t[4],
                start_seconds=2.0,
                end_seconds=8.0,
                timestamp=past_time,
                priority=t[2],
                priority_reason="Automated perimeter event.",
                review_status=t[5],
                location="Front Door" if i % 3 != 0 else "Driveway",
                confidence=0.90 + (i % 8) * 0.01,
                is_demo=True
            ))

        # Seed AI Summary
        summary = AISummary(
            video_id=demo_video.id,
            overall_summary="A person appears near the front door between 00:04 and 00:11. The individual looks at the door and then leaves the area. No additional information is available to determine their identity or purpose.",
            observations="• Subject wearing dark clothing entered front porch perimeter at 00:04.\n• Paused facing entrance door from 00:07 to 00:09.\n• Turned and exited property walkway at 00:11.\n• Background street transit observed from 00:12 to 00:16.",
            time_range="00:04 - 00:11",
            evidence="Pedestrian motion tracked along walkway; individual paused facing door handle. Silver sedan in background on roadway.",
            unknowns="Subject's identity, resident affiliation, or reason for arrival cannot be determined from video footage alone.",
            review_rationale="Activity occurred in close proximity to the front door entrance. Review if no visitor or delivery was anticipated.",
            suggested_action="Review clip and check if visitor is known to household.",
            status="Analyzed",
            model_used="Vision AI (Local)",
            objects_detected="Person, Vehicle, Door",
            created_at=datetime.datetime(2026, 10, 18, 16, 35, 0),
            is_demo=True
        )
        db.add(summary)

        # Seed Notifications
        n1 = Notification(
            title="Medium Priority: Person detected",
            message="Activity was observed near the entrance at 00:04 - 00:11.",
            priority="Medium",
            is_read=False,
            is_resolved=False,
            created_at=datetime.datetime(2026, 10, 18, 16, 33, 0)
        )
        n2 = Notification(
            title="Ring Alert: Motion detected",
            message="Front Door camera motion sensor triggered.",
            priority="Low",
            is_read=False,
            is_resolved=False,
            created_at=datetime.datetime(2026, 10, 18, 15, 10, 0)
        )
        n3 = Notification(
            title="Ring Alert: Package delivery detected",
            message="Package left on porch near Front Door.",
            priority="Low",
            is_read=False,
            is_resolved=False,
            created_at=datetime.datetime(2026, 10, 18, 14, 25, 0)
        )
        db.add_all([n1, n2, n3])

        # Seed Ring Devices if not existing
        if not db.query(RingDevice).filter(RingDevice.device_id == "ring-doorbell-pro-01").first():
            d1 = RingDevice(
                device_id="ring-doorbell-pro-01",
                name="Front Door Video Doorbell Pro",
                device_type="doorbell",
                location="Front Door",
                status="online",
                battery_level=92,
                firmware_version="v4.2.1-amazon",
                last_sync_at=datetime.datetime(2026, 10, 18, 16, 30, 0),
                is_simulator=True
            )
            db.add(d1)
        if not db.query(RingDevice).filter(RingDevice.device_id == "ring-floodlight-cam-02").first():
            d2 = RingDevice(
                device_id="ring-floodlight-cam-02",
                name="Driveway Floodlight Cam",
                device_type="floodlight",
                location="Driveway",
                status="online",
                battery_level=100,
                firmware_version="v3.8.9-amazon",
                last_sync_at=datetime.datetime(2026, 10, 18, 16, 30, 0),
                is_simulator=True
            )
            db.add(d2)

        # Seed Privacy Settings if not existing
        if not db.query(PrivacySetting).first():
            privacy = PrivacySetting(retention_days=30, auto_delete=False, blur_faces=False)
            db.add(privacy)

        db.commit()
        print("[SafeHome AI] Demo data initialized successfully.")

@app.on_event("startup")
def on_startup():
    init_db()
    db = SessionLocal()
    try:
        seed_demo_data(db)
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
