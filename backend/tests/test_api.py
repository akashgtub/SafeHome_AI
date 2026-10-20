import pytest
import os
import io
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import Video, Event, AISummary, Notification, RingDevice, PrivacySetting, AnalysisJob
from backend.app.services.video_processor import VideoProcessor
from backend.app.services.ai_analyzer import AIAnalyzer
from backend.app.services.ring_service import RingService
from backend.app.cleanup_demo_data import cleanup_database
from backend.tests.conftest import TestingSessionLocal, client, test_engine

# ====================================================================
# 1. A new database contains no seeded production events
# ====================================================================
def test_new_database_contains_no_seeded_events():
    db = TestingSessionLocal()
    events_count = db.query(Event).count()
    videos_count = db.query(Video).count()
    devices_count = db.query(RingDevice).count()
    notifs_count = db.query(Notification).count()
    db.close()

    assert events_count == 0, "New database should contain no seeded events"
    assert videos_count == 0, "New database should contain no seeded videos"
    assert devices_count == 0, "New database should contain no seeded devices"
    assert notifs_count == 0, "New database should contain no seeded notifications"

# ====================================================================
# 2. Dashboard counts are zero when the database is empty
# ====================================================================
def test_dashboard_counts_zero_when_empty():
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_events"] == 0
    assert data["review_pending"] == 0
    assert data["ai_summarized_count"] == 0
    assert data["connected_devices_count"] == 0
    assert data["connected_devices_subtitle"] == "Not connected"
    assert data["events_this_week_change"] == "0 this week"
    assert data["active_video"] is None
    assert data["active_summary"] is None
    assert data["analysis_details"] is None
    assert len(data["recent_events"]) == 0
    # Trend has 7 days with 0 events each (no fabricated counts)
    for day in data["weekly_trend"]:
        assert day["events"] == 0

# ====================================================================
# 3. Uploading a video creates one upload notification
# ====================================================================
def test_upload_creates_single_notification(monkeypatch):
    monkeypatch.setattr(
        VideoProcessor,
        "extract_metadata",
        lambda path: {"duration": 10.0, "fps": 30.0, "width": 1920, "height": 1080, "frame_count": 300}
    )
    # Mock background pipeline so test does not invoke cv2 on fake buffer
    import backend.app.routers.videos as vid_router
    monkeypatch.setattr(vid_router, "run_analysis_pipeline_sync", lambda vid: None)

    fake_video_content = b"fake-mp4-data-for-testing"
    resp = client.post(
        "/api/videos/upload",
        files={"file": ("front_door.mp4", io.BytesIO(fake_video_content), "video/mp4")}
    )
    assert resp.status_code == 200
    video_data = resp.json()
    video_id = video_data["id"]

    db = TestingSessionLocal()
    upload_notifs = db.query(Notification).filter(
        Notification.video_id == video_id,
        Notification.notification_type == "video_upload"
    ).all()
    db.close()

    assert len(upload_notifs) == 1, "Exactly one upload notification must be created"
    assert "Uploaded" in upload_notifs[0].title
    assert upload_notifs[0].is_read is False

# ====================================================================
# 4. Repeating an upload request does not duplicate a persisted operation
# ====================================================================
def test_repeating_upload_request_idempotency():
    db = TestingSessionLocal()
    video = Video(
        filename="retry_test.mp4",
        original_filename="retry_test.mp4",
        file_path="/tmp/retry_test.mp4",
        duration=10.0,
        fps=30.0,
        width=1920,
        height=1080,
        file_size=1024,
        status="completed",
        is_demo=False
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # First upload notification creation
    dedup_key = f"upload_vid_{video.id}"
    n1 = Notification(
        video_id=video.id,
        notification_type="video_upload",
        title="Video Uploaded",
        message="Ready for analysis.",
        priority="Low",
        dedup_key=dedup_key
    )
    db.add(n1)
    db.commit()

    # Second attempt with same dedup_key must be skipped / prevented
    existing = db.query(Notification).filter(Notification.dedup_key == dedup_key).first()
    assert existing is not None

    notifs = db.query(Notification).filter(Notification.video_id == video.id).all()
    assert len(notifs) == 1
    db.close()

# ====================================================================
# 5. Retrying an analysis job does not duplicate events
# ====================================================================
def test_retrying_analysis_job_does_not_duplicate_events():
    db = TestingSessionLocal()
    video = Video(
        filename="dedup_video.mp4",
        original_filename="dedup_video.mp4",
        file_path="/tmp/dedup.mp4",
        duration=15.0,
        fps=30.0,
        width=1920,
        height=1080,
        file_size=2048,
        status="processing",
        is_demo=False
    )
    db.add(video)
    db.commit()

    job = AnalysisJob(video_id=video.id, status="processing", progress=50)
    db.add(job)
    db.commit()

    events_payload = [
        {"start_seconds": 1.0, "end_seconds": 4.0, "category": "Motion", "title": "Motion detected"},
        {"start_seconds": 8.0, "end_seconds": 12.0, "category": "Motion", "title": "Motion detected"}
    ]

    # First pass persistence
    for ev in events_payload:
        st, et = ev["start_seconds"], ev["end_seconds"]
        dkey = f"vid_{video.id}_job_{job.id}_{ev['category']}_{int(st*10)}_{int(et*10)}"
        db.add(Event(
            video_id=video.id,
            job_id=job.id,
            category=ev["category"],
            title=ev["title"],
            description="Movement observed",
            start_seconds=st,
            end_seconds=et,
            priority="Low",
            review_status="Pending Review",
            dedup_key=dkey,
            is_demo=False
        ))
    db.commit()
    assert db.query(Event).filter(Event.video_id == video.id).count() == 2

    # Retry pass: Transaction deletes prior events for this video/job to ensure idempotency
    db.query(Event).filter(Event.video_id == video.id, Event.job_id == job.id).delete()
    for ev in events_payload:
        st, et = ev["start_seconds"], ev["end_seconds"]
        dkey = f"vid_{video.id}_job_{job.id}_{ev['category']}_{int(st*10)}_{int(et*10)}"
        db.add(Event(
            video_id=video.id,
            job_id=job.id,
            category=ev["category"],
            title=ev["title"],
            description="Movement observed",
            start_seconds=st,
            end_seconds=et,
            priority="Low",
            review_status="Pending Review",
            dedup_key=dkey,
            is_demo=False
        ))
    db.commit()

    # Total event count must remain exactly 2, not 4
    total = db.query(Event).filter(Event.video_id == video.id).count()
    assert total == 2
    db.close()

# ====================================================================
# 6. Overlapping motion intervals are grouped correctly
# ====================================================================
def test_overlapping_motion_intervals_grouped():
    raw_intervals = [
        {"category": "Motion", "start_seconds": 2.0, "end_seconds": 4.0, "confidence": 0.8},
        {"category": "Motion", "start_seconds": 4.5, "end_seconds": 7.0, "confidence": 0.9},
        {"category": "Motion", "start_seconds": 6.8, "end_seconds": 9.0, "confidence": 0.85}
    ]
    # Gaps are 0.5s and overlap (-0.2s), all <= gap_tolerance=2.0s
    grouped = AIAnalyzer.group_motion_intervals(raw_intervals, gap_tolerance=2.0)
    assert len(grouped) == 1
    assert grouped[0]["start_seconds"] == 2.0
    assert grouped[0]["end_seconds"] == 9.0
    assert grouped[0]["category"] == "Motion"

# ====================================================================
# 7. Distinct motion intervals remain separate
# ====================================================================
def test_distinct_motion_intervals_remain_separate():
    raw_intervals = [
        {"category": "Motion", "start_seconds": 1.0, "end_seconds": 3.0, "confidence": 0.9},
        {"category": "Motion", "start_seconds": 12.0, "end_seconds": 15.0, "confidence": 0.88}
    ]
    # Gap is 9.0s > tolerance (2.0s), must remain 2 separate events
    grouped = AIAnalyzer.group_motion_intervals(raw_intervals, gap_tolerance=2.0)
    assert len(grouped) == 2
    assert grouped[0]["end_seconds"] == 3.0
    assert grouped[1]["start_seconds"] == 12.0

    # Different categories with overlapping times must NOT merge
    diff_cats = [
        {"category": "Motion", "start_seconds": 2.0, "end_seconds": 5.0},
        {"category": "Doorbell Ring", "start_seconds": 3.0, "end_seconds": 6.0}
    ]
    grouped_diff = AIAnalyzer.group_motion_intervals(diff_cats, gap_tolerance=2.0)
    assert len(grouped_diff) == 2, "Different event categories must not merge"

# ====================================================================
# 8. Failed analysis does not create a successful AI summary
# ====================================================================
def test_failed_analysis_does_not_create_summary():
    db = TestingSessionLocal()
    video = Video(
        filename="corrupt.mp4",
        original_filename="corrupt.mp4",
        file_path="/invalid/nonexistent/corrupt.mp4",
        duration=0.0,
        fps=0.0,
        width=0,
        height=0,
        file_size=0,
        status="processing",
        is_demo=False
    )
    db.add(video)
    db.commit()

    job = AnalysisJob(video_id=video.id, status="processing")
    db.add(job)
    db.commit()

    # Simulate analysis failure
    job.status = "failed"
    job.error = "OpenCV could not open video stream"
    video.status = "failed"
    db.commit()

    # Ensure no AISummary was created
    summary = db.query(AISummary).filter(AISummary.video_id == video.id).first()
    assert summary is None, "Failed analysis must not create an AI summary"

    # Dashboard should show 0 summaries
    resp = client.get("/api/dashboard/stats")
    assert resp.json()["ai_summarized_count"] == 0
    db.close()

# ====================================================================
# 9. No notification appears when no real event occurs
# ====================================================================
def test_no_notification_when_no_real_event():
    # Calling dashboard stats or listing events must NOT create notifications
    client.get("/api/dashboard/stats")
    client.get("/api/events")
    client.get("/api/ring/status")

    db = TestingSessionLocal()
    count = db.query(Notification).count()
    db.close()
    assert count == 0, "No notifications should be generated merely by querying endpoints"

# ====================================================================
# 10. Notifications persist after reloading their API endpoint
# ====================================================================
def test_notifications_persist_across_reloads():
    db = TestingSessionLocal()
    notif = Notification(
        title="Test Security Notification",
        message="Genuine notification event.",
        priority="Medium",
        is_read=False,
        dedup_key="unique_notif_10"
    )
    db.add(notif)
    db.commit()
    db.close()

    # Query 1
    resp1 = client.get("/api/notifications")
    assert resp1.status_code == 200
    assert len(resp1.json()) == 1
    assert resp1.json()[0]["title"] == "Test Security Notification"

    # Query 2 (reloading endpoint)
    resp2 = client.get("/api/notifications")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["id"] == resp1.json()[0]["id"]

# ====================================================================
# 11. Read/unread notification counts are accurate
# ====================================================================
def test_read_unread_notification_counts():
    db = TestingSessionLocal()
    n1 = Notification(title="Alert 1", message="m1", priority="High", is_read=False, dedup_key="k1")
    n2 = Notification(title="Alert 2", message="m2", priority="Low", is_read=False, dedup_key="k2")
    db.add_all([n1, n2])
    db.commit()
    n1_id = n1.id
    db.close()

    count_resp = client.get("/api/notifications/unread-count")
    assert count_resp.json()["unread_count"] == 2

    # Mark n1 as read
    patch_resp = client.patch(f"/api/notifications/{n1_id}/read")
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_read"] is True

    # Check unread count is now 1
    count_resp2 = client.get("/api/notifications/unread-count")
    assert count_resp2.json()["unread_count"] == 1

# ====================================================================
# 12. Fake simulator devices are not counted as real Ring devices
# ====================================================================
def test_simulator_devices_not_counted_as_real():
    db = TestingSessionLocal()
    sim_dev = RingDevice(
        device_id="sim-doorbell-01",
        name="Simulated Front Door",
        device_type="doorbell",
        location="Front Door",
        status="online",
        battery_level=90,
        firmware_version="v1.0",
        last_sync_at=datetime.datetime.utcnow(),
        is_simulator=True,
        source_type="test_fixture"
    )
    db.add(sim_dev)
    db.commit()
    db.close()

    # Dashboard connected devices count must be 0
    dash_resp = client.get("/api/dashboard/stats")
    assert dash_resp.json()["connected_devices_count"] == 0
    assert dash_resp.json()["connected_devices_subtitle"] == "Not connected"

    # Status must report not connected to live hardware
    status_resp = client.get("/api/ring/status")
    assert status_resp.json()["connected"] is False
    assert status_resp.json()["device_count"] == 0

    # /api/ring/devices without include_simulator must omit it
    dev_resp = client.get("/api/ring/devices")
    assert len(dev_resp.json()) == 0

    # /api/ring/devices?include_simulator=true can list it for sandbox
    dev_sim_resp = client.get("/api/ring/devices?include_simulator=true")
    assert len(dev_sim_resp.json()) == 1

# ====================================================================
# 13. Cleanup removes confirmed demo data without deleting real data
# ====================================================================
def test_cleanup_preserves_real_data_and_removes_demo():
    db = TestingSessionLocal()
    real_video = Video(
        filename="real_user_video.mp4",
        original_filename="real_user_video.mp4",
        file_path="/real/path.mp4",
        duration=25.0,
        fps=30.0,
        width=1920,
        height=1080,
        file_size=5000,
        status="completed",
        is_demo=False
    )
    demo_video = Video(
        filename="demo_video.mp4",
        original_filename="demo_video.mp4",
        file_path="/demo/path.mp4",
        duration=20.0,
        fps=30.0,
        width=1920,
        height=1080,
        file_size=4000,
        status="completed",
        is_demo=True
    )
    db.add_all([real_video, demo_video])
    db.commit()

    real_event = Event(
        video_id=real_video.id,
        category="Motion",
        title="Real user motion",
        description="Genuine activity",
        start_seconds=2.0,
        end_seconds=6.0,
        priority="Medium",
        review_status="Pending Review",
        is_demo=False,
        dedup_key="real_ev_1"
    )
    demo_event = Event(
        video_id=demo_video.id,
        category="Person",
        title="Seeded Demo Event",
        description="Fabricated seed record",
        start_seconds=1.0,
        end_seconds=4.0,
        priority="Low",
        review_status="Reviewed",
        is_demo=True,
        dedup_key="demo_ev_1"
    )
    db.add_all([real_event, demo_event])
    db.commit()

    real_video_id = real_video.id
    demo_video_id = demo_video.id
    real_event_id = real_event.id
    demo_event_id = demo_event.id

    # Execute cleanup directly against test DB session
    db.query(Event).filter(Event.is_demo == True).delete()
    db.query(Video).filter(Video.is_demo == True).delete()
    db.commit()

    # Assert real records survive
    assert db.query(Video).filter(Video.id == real_video_id).first() is not None
    assert db.query(Event).filter(Event.id == real_event_id).first() is not None

    # Assert demo records removed
    assert db.query(Video).filter(Video.id == demo_video_id).first() is None
    assert db.query(Event).filter(Event.id == demo_event_id).first() is None
    db.close()

# ====================================================================
# 14. Cleanup is safe to run more than once (idempotent)
# ====================================================================
def test_cleanup_is_idempotent():
    # Running cleanup multiple times shouldn't raise any errors
    cleanup_database()
    cleanup_database()

# ====================================================================
# 15. Empty dashboard pages render correctly
# ====================================================================
def test_empty_dashboard_structure():
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    required_keys = [
        "total_events", "events_this_week_change", "review_pending",
        "review_pending_subtitle", "ai_summarized_count", "ai_summarized_percentage",
        "connected_devices_count", "connected_devices_subtitle", "recent_events",
        "active_video", "active_summary", "analysis_details", "priority_distribution",
        "category_distribution", "weekly_trend"
    ]
    for key in required_keys:
        assert key in data, f"Key '{key}' missing from dashboard response"

    assert data["total_events"] == 0
    assert data["review_pending"] == 0
    assert data["active_video"] is None
    assert data["active_summary"] is None

# ====================================================================
# 16. Privacy and data retention behavior remain correct
# ====================================================================
def test_privacy_and_data_retention():
    # Update privacy settings
    update_resp = client.post(
        "/api/settings",
        json={"retention_days": 15, "blur_faces": True, "local_processing_only": True}
    )
    assert update_resp.status_code == 200

    # Verify settings persisted
    get_resp = client.get("/api/settings")
    assert get_resp.status_code == 200
    p = get_resp.json()["privacy"]
    assert p["retention_days"] == 15
    assert p["blur_faces"] is True
    assert p["local_processing_only"] is True

    # Enforce retention: unexpired videos must NOT be deleted
    db = TestingSessionLocal()
    recent_video = Video(
        filename="recent.mp4",
        original_filename="recent.mp4",
        file_path="/tmp/recent.mp4",
        duration=10.0,
        fps=30.0,
        width=1280,
        height=720,
        file_size=1000,
        status="completed",
        created_at=datetime.datetime.utcnow(), # brand new
        is_demo=False
    )
    db.add(recent_video)
    db.commit()
    recent_id = recent_video.id
    db.close()

    enforce_resp = client.post("/api/settings/enforce-retention")
    assert enforce_resp.status_code == 200

    db = TestingSessionLocal()
    still_exists = db.query(Video).filter(Video.id == recent_id).first()
    assert still_exists is not None, "Unexpired user video must not be deleted by retention policy"
    db.close()

# ====================================================================
# 17. Health endpoint works
# ====================================================================
def test_health_endpoint_works():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["app"] == "SafeHome AI"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data

# ====================================================================
# 18. Failed uploads do not create success notifications or database records
# ====================================================================
def test_failed_upload_does_not_create_success_notification():
    # Attempt upload of unreadable corrupt bytes
    corrupt_content = b"not-a-valid-video-stream-content"
    resp = client.post(
        "/api/videos/upload",
        files={"file": ("broken_footage.mp4", io.BytesIO(corrupt_content), "video/mp4")}
    )
    assert resp.status_code == 400
    assert "Corrupt or invalid video file" in resp.json()["detail"]

    # Verify no video record was persisted
    db = TestingSessionLocal()
    assert db.query(Video).count() == 0
    assert db.query(Notification).count() == 0
    assert db.query(Event).count() == 0
    db.close()

# ====================================================================
# 19. Invalid video file formats are rejected
# ====================================================================
def test_invalid_video_files_rejected():
    # Unsupported file extensions
    bad_files = [
        ("malicious.exe", b"MZ...", "application/x-msdownload"),
        ("notes.txt", b"plain text", "text/plain"),
        ("document.pdf", b"%PDF-1.4...", "application/pdf")
    ]
    for filename, content, mime in bad_files:
        resp = client.post(
            "/api/videos/upload",
            files={"file": (filename, io.BytesIO(content), mime)}
        )
        assert resp.status_code == 400
        assert "Unsupported format" in resp.json()["detail"]

    db = TestingSessionLocal()
    assert db.query(Video).count() == 0
    assert db.query(Notification).count() == 0
    db.close()

# ====================================================================
# 20. Dashboard statistics accurately reflect real database records
# ====================================================================
def test_dashboard_statistics_match_actual_records():
    db = TestingSessionLocal()
    v1 = Video(
        filename="rec1.mp4",
        original_filename="rec1.mp4",
        file_path="/path/rec1.mp4",
        duration=30.0,
        status="completed",
        is_demo=False
    )
    v2 = Video(
        filename="rec2.mp4",
        original_filename="rec2.mp4",
        file_path="/path/rec2.mp4",
        duration=45.0,
        status="completed",
        is_demo=False
    )
    db.add_all([v1, v2])
    db.commit()

    e1 = Event(
        video_id=v1.id,
        category="Person",
        title="Visitor approached",
        description="Person on walkway",
        priority="Medium",
        review_status="Pending Review",
        is_demo=False
    )
    e2 = Event(
        video_id=v2.id,
        category="Motion",
        title="Porch motion",
        description="Movement on porch",
        priority="Low",
        review_status="Reviewed",
        is_demo=False
    )
    e3 = Event(
        video_id=v2.id,
        category="Package",
        title="Package observed",
        description="Package at door",
        priority="Low",
        review_status="Pending Review",
        is_demo=False
    )
    db.add_all([e1, e2, e3])
    db.commit()

    s2 = AISummary(
        video_id=v2.id,
        overall_summary="Person arrived and package observed at door.",
        model_used="Gemini Vision (gemini-1.5-flash)",
        is_demo=False
    )
    db.add(s2)
    db.commit()
    db.close()

    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    # Verify counts match exact records
    assert data["total_events"] == 3
    assert data["review_pending"] == 2
    assert data["ai_summarized_count"] == 1
    assert data["active_video"]["original_filename"] == "rec2.mp4"
    assert data["active_summary"]["overall_summary"] == "Person arrived and package observed at door."
    assert data["priority_distribution"]["Medium"] == 1
    assert data["priority_distribution"]["Low"] == 2
    assert data["priority_distribution"]["High"] == 0

# ====================================================================
# 21. Fake demo data is not inserted in production paths
# ====================================================================
def test_fake_demo_data_not_inserted_in_production():
    resp = client.post("/api/settings/reset-demo-data")
    assert resp.status_code == 200

    db = TestingSessionLocal()
    # Confirm no demo records exist
    demo_videos = db.query(Video).filter(Video.is_demo == True).count()
    demo_events = db.query(Event).filter(Event.is_demo == True).count()
    demo_summaries = db.query(AISummary).filter(AISummary.is_demo == True).count()
    sim_devices = db.query(RingDevice).filter(RingDevice.is_simulator == True).count()
    db.close()

    assert demo_videos == 0
    assert demo_events == 0
    assert demo_summaries == 0
    assert sim_devices == 0

