import os
import json
import io
import datetime
import pytest
import numpy as np
import cv2
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import Video, Event, AISummary, Notification, RingDevice, PrivacySetting, AnalysisJob
from backend.app.config import settings
from backend.app.services.video_processor import VideoProcessor
from backend.app.services.ai_analyzer import AIAnalyzer
from backend.app.schemas import VisionAnalysisOutput, VisionActivityItem
import backend.app.routers.videos as vid_router

from backend.tests.conftest import (
    test_engine,
    TestingSessionLocal,
    client
)

def create_sample_frame_image(target_path: str, add_face: bool = False):
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    img = np.ones((480, 640, 3), dtype=np.uint8) * 120
    if add_face:
        # Draw a synthetic face
        cv2.circle(img, (320, 240), 60, (200, 180, 150), -1)
        cv2.circle(img, (300, 220), 8, (30, 30, 30), -1)
        cv2.circle(img, (340, 220), 8, (30, 30, 30), -1)
        cv2.ellipse(img, (320, 260), (25, 10), 0, 0, 180, (20, 20, 100), 3)
    cv2.imwrite(target_path, img)
    return target_path

# ====================================================================
# 1. Video frames are actually passed to configured vision provider
# ====================================================================
@pytest.mark.anyio
async def test_frames_passed_to_configured_vision_provider(monkeypatch, tmp_path):
    frame1 = str(tmp_path / "f1.jpg")
    frame2 = str(tmp_path / "f2.jpg")
    create_sample_frame_image(frame1)
    create_sample_frame_image(frame2)

    sampled = [
        {"timestamp_sec": 1.0, "time_str": "00:01", "frame_path": frame1, "frame_url": "/api/videos/frames/1/f1.jpg", "motion_detected": True, "motion_score": 0.5},
        {"timestamp_sec": 4.0, "time_str": "00:04", "frame_path": frame2, "frame_url": "/api/videos/frames/1/f2.jpg", "motion_detected": True, "motion_score": 0.6}
    ]
    meta = {"duration": 10.0, "fps": 30.0, "width": 640, "height": 480}

    # Test Gemini Request Structure
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")

    gemini_called_payload = {}

    class MockGeminiResponse:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return {
                "candidates": [{
                    "content": {
                        "parts": [{
                            "text": json.dumps({
                                "summary": "A person walked past the camera.",
                                "observed_activities": ["Person observed at 00:04"],
                                "important_time_ranges": ["00:01 - 00:04"],
                                "unknown_information": "Identity unverified",
                                "recommended_review_action": "Check clip",
                                "activities": [{
                                    "start_time_seconds": 1.0,
                                    "end_time_seconds": 4.0,
                                    "category": "Person",
                                    "description": "Person in walkway",
                                    "evidence": "Visible in keyframes 1 and 2",
                                    "confidence": 0.94,
                                    "review_priority": "Medium"
                                }]
                            })
                        }]
                    }
                }]
            }

    async def mock_post(self, url, **kwargs):
        nonlocal gemini_called_payload
        gemini_called_payload = kwargs.get("json", {})
        return MockGeminiResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    events, summary, model_name = await AIAnalyzer.analyze_video_frames(meta, sampled)

    assert "gemini" in model_name.lower()
    assert "contents" in gemini_called_payload
    parts = gemini_called_payload["contents"][0]["parts"]
    image_parts = [p for p in parts if "inline_data" in p]
    assert len(image_parts) >= 2
    assert image_parts[0]["inline_data"]["mime_type"] == "image/jpeg"
    assert len(image_parts[0]["inline_data"]["data"]) > 100

# ====================================================================
# 2. Real provider output is validated and persisted
# ====================================================================
def test_real_provider_output_validated_and_persisted(monkeypatch, tmp_path):
    frame1 = str(tmp_path / "f1.jpg")
    create_sample_frame_image(frame1)

    db = TestingSessionLocal()
    vid = Video(
        filename="test_vid.mp4",
        original_filename="test_vid.mp4",
        file_path=frame1,
        duration=15.0,
        fps=30.0,
        width=640,
        height=480,
        status="processing"
    )
    db.add(vid)
    db.commit()
    job = AnalysisJob(video_id=vid.id, status="queued")
    db.add(job)
    db.commit()
    vid_id = vid.id
    db.close()

    monkeypatch.setattr(VideoProcessor, "extract_metadata", lambda p: {"duration": 15.0, "fps": 30.0, "width": 640, "height": 480})
    monkeypatch.setattr(VideoProcessor, "sample_frames_and_detect_motion", lambda *a, **kw: [
        {"timestamp_sec": 4.0, "time_str": "00:04", "frame_path": frame1, "frame_url": "/api/videos/frames/1/f1.jpg", "motion_detected": True, "motion_score": 0.5}
    ])

    fake_vision_output = VisionAnalysisOutput(
        summary="A delivery worker approached entrance with a parcel.",
        observed_activities=["Person walked to porch at 00:04"],
        important_time_ranges=["00:04 - 00:08"],
        unknown_information="Company name and recipient name not visible",
        recommended_review_action="Check package at front porch",
        activities=[
            VisionActivityItem(
                start_time_seconds=4.0,
                end_time_seconds=8.0,
                category="Person",
                description="Delivery worker approaches front porch.",
                evidence="Visible holding box at timestamp 00:04.",
                confidence=0.91,
                uncertainty="Courier identity is unverified.",
                review_priority="Medium",
                priority_reason="Visitor at entrance door.",
                location="Front Door"
            )
        ]
    )

    async def mock_analyze(*args, **kwargs):
        evs = [{
            "title": "Person detected (00:04 - 00:08)",
            "category": "Person",
            "start_time": "00:04",
            "end_time": "00:08",
            "start_seconds": 4.0,
            "end_seconds": 8.0,
            "description": "Delivery worker approaches front porch.",
            "priority": "Medium",
            "priority_reason": "Visitor at entrance door.",
            "location": "Front Door",
            "confidence": 0.91,
            "uncertainty": "Courier identity is unverified.",
            "raw_evidence": "Visible holding box at timestamp 00:04.",
            "thumbnail_path": "/api/videos/frames/1/f1.jpg",
            "detection_mode": "AI Visual Analysis",
            "source": "vision_ai"
        }]
        summary = {
            "overall_summary": fake_vision_output.summary,
            "observations": "• Person walked to porch at 00:04",
            "time_range": "00:04 - 00:08",
            "evidence": "Analyzed keyframes via Gemini Vision.",
            "unknowns": fake_vision_output.unknown_information,
            "uncertainty_limitations": fake_vision_output.unknown_information,
            "review_rationale": "Visitor near entrance.",
            "suggested_action": fake_vision_output.recommended_review_action,
            "objects_detected": "Person",
            "frames_sampled": 1
        }
        return evs, summary, "Gemini Vision (gemini-1.5-flash)"

    monkeypatch.setattr(AIAnalyzer, "analyze_video_frames", mock_analyze)

    vid_router.run_analysis_pipeline_sync(vid_id)

    db = TestingSessionLocal()
    saved_vid = db.query(Video).filter(Video.id == vid_id).first()
    saved_job = db.query(AnalysisJob).filter(AnalysisJob.video_id == vid_id).first()
    saved_events = db.query(Event).filter(Event.video_id == vid_id).all()
    saved_summary = db.query(AISummary).filter(AISummary.video_id == vid_id).first()
    db.close()

    assert saved_vid.status == "completed"
    assert saved_job.status == "completed"
    assert len(saved_events) == 1
    ev = saved_events[0]
    assert ev.category == "Person"
    assert ev.start_seconds == 4.0
    assert ev.end_seconds == 8.0
    assert ev.confidence == 0.91
    assert ev.detection_mode == "AI Visual Analysis"
    assert "Courier identity" in ev.uncertainty

    assert saved_summary is not None
    assert "delivery worker" in saved_summary.overall_summary.lower()
    assert saved_summary.frames_sampled == 1

# ====================================================================
# 3. Missing API credentials produce an explicit configuration error
# ====================================================================
@pytest.mark.anyio
async def test_missing_api_credentials_produce_explicit_error(monkeypatch):
    meta = {"duration": 10.0, "fps": 30.0, "width": 640, "height": 480}
    sampled = [{"timestamp_sec": 1.0, "time_str": "00:01", "frame_path": "fake.jpg", "motion_detected": False}]

    # Gemini without key
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    with pytest.raises(ValueError) as exc:
        await AIAnalyzer.analyze_video_frames(meta, sampled, local_processing_only=False)
    assert "Gemini API key is not configured" in str(exc.value)

    # OpenAI without key
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

    with pytest.raises(ValueError) as exc2:
        await AIAnalyzer.analyze_video_frames(meta, sampled, local_processing_only=False)
    assert "OpenAI API key is not configured" in str(exc2.value)

    # Provider == "mock" without local_processing_only
    monkeypatch.setattr(settings, "AI_PROVIDER", "mock")
    with pytest.raises(ValueError) as exc3:
        await AIAnalyzer.analyze_video_frames(meta, sampled, local_processing_only=False)
    assert "No supported AI vision provider is configured" in str(exc3.value)

# ====================================================================
# 4. Provider failures do not generate fake summaries
# ====================================================================
def test_provider_failures_do_not_generate_fake_summaries(monkeypatch, tmp_path):
    frame1 = str(tmp_path / "f1.jpg")
    create_sample_frame_image(frame1)

    db = TestingSessionLocal()
    vid = Video(filename="fail.mp4", original_filename="fail.mp4", file_path=frame1, status="processing")
    db.add(vid)
    db.commit()
    job = AnalysisJob(video_id=vid.id, status="queued")
    db.add(job)
    db.commit()
    vid_id = vid.id
    db.close()

    monkeypatch.setattr(VideoProcessor, "extract_metadata", lambda p: {"duration": 10.0, "fps": 30.0, "width": 640, "height": 480})
    monkeypatch.setattr(VideoProcessor, "sample_frames_and_detect_motion", lambda *a, **kw: [
        {"timestamp_sec": 1.0, "time_str": "00:01", "frame_path": frame1, "motion_detected": True}
    ])

    async def mock_failing_analyze(*args, **kwargs):
        raise ValueError("Simulated Gemini API rate limit or outage")

    monkeypatch.setattr(AIAnalyzer, "analyze_video_frames", mock_failing_analyze)

    vid_router.run_analysis_pipeline_sync(vid_id)

    db = TestingSessionLocal()
    failed_vid = db.query(Video).filter(Video.id == vid_id).first()
    failed_job = db.query(AnalysisJob).filter(AnalysisJob.video_id == vid_id).first()
    summary_count = db.query(AISummary).filter(AISummary.video_id == vid_id).count()
    events_count = db.query(Event).filter(Event.video_id == vid_id).count()
    db.close()

    assert failed_vid.status == "failed"
    assert "Simulated Gemini" in failed_vid.error_message
    assert failed_job.status == "failed"
    assert summary_count == 0, "No summary must be created on provider failure"
    assert events_count == 0, "No fake events must be created on provider failure"

# ====================================================================
# 5. Local-only mode never calls an external provider
# ====================================================================
@pytest.mark.anyio
async def test_local_only_mode_never_calls_external_provider(monkeypatch, tmp_path):
    frame1 = str(tmp_path / "f1.jpg")
    create_sample_frame_image(frame1)

    sampled = [
        {"timestamp_sec": 2.0, "time_str": "00:02", "frame_path": frame1, "frame_url": "/frame.jpg", "motion_detected": True, "motion_score": 0.4}
    ]
    meta = {"duration": 10.0, "fps": 30.0, "width": 640, "height": 480}

    async def forbidden_post(self, *args, **kwargs):
        raise AssertionError("External network call made during local_processing_only mode!")

    monkeypatch.setattr(httpx.AsyncClient, "post", forbidden_post)

    events, summary, model_label = await AIAnalyzer.analyze_video_frames(
        video_metadata=meta,
        sampled_frames=sampled,
        local_processing_only=True
    )

    assert "Local Edge CV" in model_label
    assert "Zero Cloud Transmission" in model_label
    assert len(events) >= 1
    assert events[0]["detection_mode"] == "Local Motion Analysis"
    assert "Motion" in events[0]["category"]

# ====================================================================
# 6. Face anonymization is applied before cloud transmission when enabled
# ====================================================================
def test_face_anonymization_applied_before_cloud_transmission(tmp_path):
    frame_path = str(tmp_path / "face.jpg")
    create_sample_frame_image(frame_path, add_face=True)

    original_img = cv2.imread(frame_path)
    roi_original = original_img[180:300, 260:380].copy()

    blurred_frame, count = VideoProcessor.anonymize_frame(original_img)
    assert isinstance(blurred_frame, np.ndarray)
    assert blurred_frame.shape == original_img.shape

    # Verify Gaussian blur decreases high-frequency gradient variance
    ksize = 25
    synthetic_blur = cv2.GaussianBlur(roi_original, (ksize, ksize), 45)
    assert float(np.var(synthetic_blur)) <= float(np.var(roi_original))

# ====================================================================
# 7. Timestamps correspond to sampled video frames
# ====================================================================
@pytest.mark.anyio
async def test_timestamps_correspond_to_sampled_video_frames(monkeypatch, tmp_path):
    f1 = str(tmp_path / "f1.jpg")
    f2 = str(tmp_path / "f2.jpg")
    f3 = str(tmp_path / "f3.jpg")
    create_sample_frame_image(f1)
    create_sample_frame_image(f2)
    create_sample_frame_image(f3)

    sampled = [
        {"timestamp_sec": 3.0, "time_str": "00:03", "frame_path": f1, "frame_url": "/f1.jpg", "motion_detected": True},
        {"timestamp_sec": 7.0, "time_str": "00:07", "frame_path": f2, "frame_url": "/f2.jpg", "motion_detected": True},
        {"timestamp_sec": 12.0, "time_str": "00:12", "frame_path": f3, "frame_url": "/f3.jpg", "motion_detected": False}
    ]
    meta = {"duration": 15.0, "fps": 30.0, "width": 640, "height": 480}

    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")

    mock_json_resp = {
        "summary": "Vehicle drove past.",
        "observed_activities": ["Vehicle at 00:07"],
        "important_time_ranges": ["00:07 - 00:12"],
        "unknown_information": "License plate unseen",
        "recommended_review_action": "Routine",
        "activities": [{
            "start_time_seconds": 7.0,
            "end_time_seconds": 12.0,
            "category": "Vehicle",
            "description": "Sedan passing by.",
            "evidence": "Frame at 00:07 and 00:12",
            "confidence": 0.88,
            "review_priority": "Low"
        }]
    }

    class MockResp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": json.dumps(mock_json_resp)}]}}]}

    async def mock_post(self, *args, **kwargs):
        return MockResp()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    events, summary, model = await AIAnalyzer.analyze_video_frames(meta, sampled)
    vehicle_events = [e for e in events if e.get("category") == "Vehicle"]
    assert len(vehicle_events) == 1
    v_ev = vehicle_events[0]
    assert v_ev["start_time"] == "00:07"
    assert v_ev["end_time"] == "00:12"
    assert v_ev["start_seconds"] == 7.0
    assert v_ev["end_seconds"] == 12.0
    assert v_ev["thumbnail_path"] == "/f2.jpg"

# ====================================================================
# 8. Malformed model output is rejected safely
# ====================================================================
@pytest.mark.anyio
async def test_malformed_model_output_rejected_safely(monkeypatch, tmp_path):
    f1 = str(tmp_path / "f1.jpg")
    create_sample_frame_image(f1)
    sampled = [{"timestamp_sec": 1.0, "time_str": "00:01", "frame_path": f1, "frame_url": "/f1.jpg", "motion_detected": True}]
    meta = {"duration": 5.0, "fps": 30.0, "width": 640, "height": 480}

    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")

    class MalformedResp1:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "I see a person walking outside! Nice video."}]}}]}

    async def mock_post_malformed1(self, *args, **kwargs):
        return MalformedResp1()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_malformed1)
    with pytest.raises(ValueError) as exc1:
        await AIAnalyzer.analyze_video_frames(meta, sampled)
    assert "invalid json" in str(exc1.value).lower()

    class MalformedResp2:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": json.dumps({"unknown_information": "none", "activities": "broken"})}]}}]}

    async def mock_post_malformed2(self, *args, **kwargs):
        return MalformedResp2()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_malformed2)
    with pytest.raises(ValueError) as exc2:
        await AIAnalyzer.analyze_video_frames(meta, sampled)
    assert "schema validation" in str(exc2.value).lower()

# ====================================================================
# 9. Duplicate activities are not persisted repeatedly
# ====================================================================
def test_duplicate_activities_consolidated():
    raw_activities = [
        VisionActivityItem(
            start_time_seconds=4.0,
            end_time_seconds=6.0,
            category="Person",
            description="Person walking on pathway",
            evidence="Keyframe 1",
            confidence=0.90,
            review_priority="Low"
        ),
        VisionActivityItem(
            start_time_seconds=6.5,
            end_time_seconds=9.0,
            category="Person",
            description="Person walking toward entrance",
            evidence="Keyframe 2",
            confidence=0.92,
            review_priority="Medium"
        ),
        VisionActivityItem(
            start_time_seconds=15.0,
            end_time_seconds=18.0,
            category="Vehicle",
            description="Car driving by",
            evidence="Keyframe 3",
            confidence=0.88,
            review_priority="Low"
        )
    ]

    consolidated = AIAnalyzer.consolidate_vision_activities(raw_activities, gap_tolerance=2.0)
    assert len(consolidated) == 2
    person_act = [a for a in consolidated if a.category == "Person"][0]
    assert person_act.start_time_seconds == 4.0
    assert person_act.end_time_seconds == 9.0
    assert person_act.review_priority == "Medium"
    assert "Keyframe 1; Keyframe 2" in person_act.evidence

# ====================================================================
# 10. Reanalysis does not create duplicate events
# ====================================================================
def test_reanalysis_does_not_create_duplicate_events(monkeypatch, tmp_path):
    frame1 = str(tmp_path / "f1.jpg")
    create_sample_frame_image(frame1)

    db = TestingSessionLocal()
    vid = Video(filename="reanalysis.mp4", original_filename="reanalysis.mp4", file_path=frame1, status="completed", duration=10.0)
    db.add(vid)
    db.commit()
    job = AnalysisJob(video_id=vid.id, status="completed")
    db.add(job)
    db.commit()
    vid_id = vid.id
    db.close()

    monkeypatch.setattr(VideoProcessor, "extract_metadata", lambda p: {"duration": 10.0, "fps": 30.0, "width": 640, "height": 480})
    monkeypatch.setattr(VideoProcessor, "sample_frames_and_detect_motion", lambda *a, **kw: [
        {"timestamp_sec": 2.0, "time_str": "00:02", "frame_path": frame1, "motion_detected": True, "motion_score": 0.5}
    ])

    async def mock_analyze(*args, **kwargs):
        evs = [{
            "title": "Person detected (00:02 - 00:05)",
            "category": "Person",
            "start_time": "00:02",
            "end_time": "00:05",
            "start_seconds": 2.0,
            "end_seconds": 5.0,
            "description": "Person at door",
            "priority": "Medium",
            "confidence": 0.90,
            "detection_mode": "AI Visual Analysis",
            "source": "vision_ai"
        }]
        summary = {"overall_summary": "Visitor seen.", "status": "Analyzed", "objects_detected": "Person", "frames_sampled": 1}
        return evs, summary, "Gemini Vision"

    monkeypatch.setattr(AIAnalyzer, "analyze_video_frames", mock_analyze)

    # Run analysis first time
    vid_router.run_analysis_pipeline_sync(vid_id)

    db = TestingSessionLocal()
    count_first = db.query(Event).filter(Event.video_id == vid_id).count()
    assert count_first == 1
    db.close()

    # Re-run analysis second time
    vid_router.run_analysis_pipeline_sync(vid_id)

    db = TestingSessionLocal()
    count_second = db.query(Event).filter(Event.video_id == vid_id).count()
    summary_count = db.query(AISummary).filter(AISummary.video_id == vid_id).count()
    db.close()

    assert count_second == 1, "Reanalysis must not duplicate events"
    assert summary_count == 1, "Reanalysis must not duplicate summaries"

# ====================================================================
# 11. Empty videos and unsupported files are handled correctly
# ====================================================================
def test_empty_and_unsupported_video_files_handled(tmp_path):
    resp_ext = client.post(
        "/api/videos/upload",
        files={"file": ("invalid.txt", io.BytesIO(b"not a video"), "text/plain")}
    )
    assert resp_ext.status_code == 400
    assert "Unsupported format" in resp_ext.json()["detail"]

    resp_corrupt = client.post(
        "/api/videos/upload",
        files={"file": ("corrupt.mp4", io.BytesIO(b"not real mp4 header"), "video/mp4")}
    )
    assert resp_corrupt.status_code == 400
    assert "Corrupt or invalid video file" in resp_corrupt.json()["detail"]

# ====================================================================
# 12. Frontend API / Dashboard displays actual analysis responses
# ====================================================================
def test_frontend_api_displays_actual_analysis_responses(tmp_path):
    db = TestingSessionLocal()
    vid = Video(
        filename="real_clip.mp4",
        original_filename="real_clip.mp4",
        file_path="/path/real_clip.mp4",
        duration=22.0,
        fps=30.0,
        width=1920,
        height=1080,
        status="completed"
    )
    db.add(vid)
    db.commit()

    job = AnalysisJob(
        video_id=vid.id,
        status="completed",
        frames_analyzed=8,
        model_used="Gemini Vision (gemini-1.5-flash)"
    )
    db.add(job)

    ev1 = Event(
        video_id=vid.id,
        job_id=job.id,
        category="Person",
        title="Person detected (00:04 - 00:10)",
        description="Individual walked to porch.",
        start_time="00:04",
        end_time="00:10",
        start_seconds=4.0,
        end_seconds=10.0,
        priority="Medium",
        confidence=0.93,
        uncertainty="Identity cannot be determined.",
        detection_mode="AI Visual Analysis",
        source="vision_ai",
        is_demo=False
    )
    ev2 = Event(
        video_id=vid.id,
        job_id=job.id,
        category="Motion",
        title="Motion detected (00:04 - 00:10)",
        description="Foreground optical motion detected.",
        start_time="00:04",
        end_time="00:10",
        start_seconds=4.0,
        end_seconds=10.0,
        priority="Low",
        detection_mode="Local Motion Analysis",
        source="local_motion_cv",
        is_demo=False
    )
    db.add(ev1)
    db.add(ev2)

    summary = AISummary(
        video_id=vid.id,
        overall_summary="A person approached the front entrance and departed.",
        observations="• Person observed near door from 00:04 to 00:10",
        time_range="00:04 - 00:10",
        evidence="Analyzed 8 sampled keyframes.",
        unknowns="Identity and intention unverified.",
        uncertainty_limitations="Identity and intention unverified.",
        model_used="Gemini Vision (gemini-1.5-flash)",
        objects_detected="Person",
        frames_sampled=8,
        status="Analyzed",
        is_demo=False
    )
    db.add(summary)
    db.commit()
    db.close()

    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_events"] == 2
    assert data["active_video"]["status"] == "completed"
    assert data["active_summary"]["overall_summary"] == "A person approached the front entrance and departed."
    assert data["active_summary"]["frames_sampled"] == 8

    details = data["analysis_details"]
    assert details["frames_analyzed"] == "8 frames"
    assert "Gemini" in details["analysis_mode"]
    assert details["analysis_status"] == "completed"

    ev_resp = client.get("/api/events")
    assert ev_resp.status_code == 200
    ev_list = ev_resp.json()
    modes = [e["detection_mode"] for e in ev_list]
    assert "AI Visual Analysis" in modes
    assert "Local Motion Analysis" in modes

# ====================================================================
# 13. Analysis failures are displayed accurately in dashboard API
# ====================================================================
def test_analysis_failures_displayed_accurately():
    db = TestingSessionLocal()
    vid = Video(
        filename="failed_run.mp4",
        original_filename="failed_run.mp4",
        file_path="/path/failed_run.mp4",
        duration=10.0,
        status="failed",
        error_message="Gemini API key is not configured.",
        is_demo=False
    )
    db.add(vid)
    db.commit()

    job = AnalysisJob(
        video_id=vid.id,
        status="failed",
        error="Gemini API key is not configured."
    )
    db.add(job)
    db.commit()
    db.close()

    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()

    assert data["active_video"]["status"] == "failed"
    assert "Gemini API key is not configured" in data["active_video"]["error_message"]
    assert data["active_summary"] is None
    assert data["analysis_details"]["analysis_status"] == "failed"
    assert "Gemini API key is not configured" in data["analysis_details"]["error_message"]

# ====================================================================
# 14. Existing privacy and retention tests still pass
# ====================================================================
def test_privacy_and_retention_preserved():
    resp = client.post("/api/settings", json={
        "retention_days": 7,
        "blur_faces": True,
        "local_processing_only": True
    })
    assert resp.status_code == 200

    get_resp = client.get("/api/settings")
    assert get_resp.status_code == 200
    p = get_resp.json()["privacy"]
    assert p["retention_days"] == 7
    assert p["blur_faces"] is True
    assert p["local_processing_only"] is True
