import os
import uuid
import shutil
import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Video, AnalysisJob, Event, AISummary, Notification
from ..config import settings
from ..schemas import VideoResponse, AnalysisJobResponse
from ..services.video_processor import VideoProcessor
from ..services.ai_analyzer import AIAnalyzer

router = APIRouter(prefix="/api/videos", tags=["Videos"])

def run_analysis_pipeline_sync(video_id: int):
    """
    Background worker that runs OpenCV frame sampling and AI analysis.
    Uses its own db session.
    """
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        video = db.query(Video).filter(Video.id == video_id).first()
        job = db.query(AnalysisJob).filter(AnalysisJob.video_id == video_id).first()
        if not video or not job:
            return

        job.status = "running"
        job.progress = 10
        db.commit()

        # Step 1: Extract metadata
        meta = VideoProcessor.extract_metadata(video.file_path)
        video.duration = meta["duration"]
        video.width = meta["width"]
        video.height = meta["height"]
        video.fps = meta["fps"]
        job.progress = 25
        db.commit()

        # Step 2: Sample frames and detect motion
        def update_progress(pct):
            job.progress = 25 + int(pct * 0.45) # 25% -> 55%
            db.commit()

        sampled = VideoProcessor.sample_frames_and_detect_motion(
            video_id=video.id,
            file_path=video.file_path,
            sample_interval_sec=1.0,
            progress_callback=update_progress
        )

        job.frames_analyzed = len(sampled)
        job.progress = 60
        db.commit()

        # Step 3: Run AI frame analysis (Gemini / OpenAI / Local CV Fallback)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        events_data, summary_data, model_name = loop.run_until_complete(
            AIAnalyzer.analyze_video_frames(meta, sampled, is_demo=video.is_demo)
        )
        loop.close()

        job.model_used = model_name
        job.progress = 80
        db.commit()

        # Step 4: Persist events
        # Clear any prior events for this video
        db.query(Event).filter(Event.video_id == video.id).delete()
        for idx, ev in enumerate(events_data):
            thumbnail = ev.get("thumbnail_path")
            if not thumbnail and sampled:
                # pick frame closest to start time
                st = ev.get("start_seconds", 0.0)
                closest = min(sampled, key=lambda x: abs(x["timestamp_sec"] - st))
                thumbnail = closest["frame_url"]

            new_event = Event(
                video_id=video.id,
                source="uploaded_video",
                category=ev.get("category", "Motion"),
                title=ev.get("title", f"Event #{idx+1}"),
                description=ev.get("description", "Activity observed."),
                start_time=ev.get("start_time", "00:00"),
                end_time=ev.get("end_time", "00:05"),
                start_seconds=ev.get("start_seconds", 0.0),
                end_seconds=ev.get("end_seconds", 5.0),
                priority=ev.get("priority", "Low"),
                priority_reason=ev.get("priority_reason", "Routine observation."),
                review_status="Pending Review",
                location=ev.get("location", "Front Door"),
                confidence=ev.get("confidence", 0.92),
                thumbnail_path=thumbnail,
                raw_evidence=ev.get("raw_evidence", ""),
                is_demo=video.is_demo
            )
            db.add(new_event)
            db.commit()

            # Create notification for review
            notif = Notification(
                event_id=new_event.id,
                title=f"{new_event.priority} Priority: {new_event.title}",
                message=f"At {new_event.start_time}: {new_event.description}",
                priority=new_event.priority,
                is_read=False,
                is_resolved=False
            )
            db.add(notif)
            db.commit()

        # Step 5: Persist AI Summary
        db.query(AISummary).filter(AISummary.video_id == video.id).delete()
        ai_summary = AISummary(
            video_id=video.id,
            overall_summary=summary_data.get("overall_summary", "Video processed."),
            observations=summary_data.get("observations", ""),
            time_range=summary_data.get("time_range", f"00:00 - {int(video.duration//60):02d}:{int(video.duration%60):02d}"),
            evidence=summary_data.get("evidence", ""),
            unknowns=summary_data.get("unknowns", ""),
            review_rationale=summary_data.get("review_rationale", "Routine check."),
            suggested_action=summary_data.get("suggested_action", "Review clip if unexpected."),
            status="Analyzed",
            model_used=model_name,
            objects_detected=summary_data.get("objects_detected", "Person, Door"),
            is_demo=video.is_demo
        )
        db.add(ai_summary)

        video.status = "completed"
        job.status = "completed"
        job.progress = 100
        db.commit()

    except Exception as e:
        import traceback
        traceback.print_exc()
        if video:
            video.status = "failed"
            video.error_message = str(e)
        if job:
            job.status = "failed"
            job.error = str(e)
        db.commit()
    finally:
        db.close()

@router.post("/upload", response_model=VideoResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    valid, msg = VideoProcessor.validate_file(file.filename, 0)
    if not valid and "Unsupported format" in msg:
        raise HTTPException(status_code=400, detail=msg)

    # Secure unique filename
    unique_name = f"{uuid.uuid4().hex[:12]}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    # Save to disk
    file_size = 0
    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024): # 1MB chunks
            file_size += len(chunk)
            if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                buffer.close()
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"Video exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                )
            buffer.write(chunk)

    # Validate video readability & duration with OpenCV
    try:
        meta = VideoProcessor.extract_metadata(file_path)
        if meta["duration"] > settings.MAX_VIDEO_DURATION_SECONDS:
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=f"Video duration ({meta['duration']}s) exceeds maximum of {settings.MAX_VIDEO_DURATION_SECONDS}s."
            )
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Corrupt or invalid video file: {str(e)}")

    # Create video record
    video = Video(
        filename=unique_name,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        duration=meta["duration"],
        width=meta["width"],
        height=meta["height"],
        fps=meta["fps"],
        status="processing",
        is_demo=False
    )
    db.add(video)
    db.commit()
    db.refresh(video)

    # Create analysis job
    job = AnalysisJob(
        video_id=video.id,
        status="queued",
        progress=0,
        model_used=settings.AI_PROVIDER
    )
    db.add(job)
    db.commit()

    # Launch background processing
    background_tasks.add_task(run_analysis_pipeline_sync, video.id)

    resp = VideoResponse.model_validate(video)
    resp.stream_url = f"/api/videos/stream/{video.id}"
    return resp

@router.get("", response_model=List[VideoResponse])
def list_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).order_by(Video.id.desc()).all()
    results = []
    for v in videos:
        vr = VideoResponse.model_validate(v)
        vr.stream_url = f"/api/videos/stream/{v.id}"
        results.append(vr)
    return results

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    vr = VideoResponse.model_validate(video)
    vr.stream_url = f"/api/videos/stream/{video.id}"
    return vr

@router.get("/{video_id}/status", response_model=AnalysisJobResponse)
def get_analysis_status(video_id: int, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter(AnalysisJob.video_id == video_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.post("/{video_id}/analyze")
def trigger_video_analysis(
    video_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video.status = "processing"
    job = db.query(AnalysisJob).filter(AnalysisJob.video_id == video_id).first()
    if not job:
        job = AnalysisJob(video_id=video.id, status="queued", progress=0)
        db.add(job)
    else:
        job.status = "queued"
        job.progress = 0
        job.error = None
    db.commit()

    background_tasks.add_task(run_analysis_pipeline_sync, video.id)
    return {"message": "Analysis started", "video_id": video.id}

@router.delete("/{video_id}")
def delete_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Clean up disk files
    try:
        if os.path.exists(video.file_path):
            os.remove(video.file_path)
        frame_dir = os.path.join(settings.FRAMES_DIR, f"vid_{video.id}")
        if os.path.exists(frame_dir):
            shutil.rmtree(frame_dir)
    except Exception as e:
        print(f"Error deleting files: {e}")

    db.delete(video)
    db.commit()
    return {"message": "Video and associated analysis data deleted successfully"}

@router.get("/stream/{video_id}")
def stream_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video or not os.path.exists(video.file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    return FileResponse(video.file_path, media_type="video/mp4")

@router.get("/frames/{video_id}/{filename}")
def serve_frame(video_id: int, filename: str):
    file_path = os.path.join(settings.FRAMES_DIR, f"vid_{video_id}", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(file_path, media_type="image/jpeg")
