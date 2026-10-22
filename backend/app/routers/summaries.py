from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AISummary, Video, AnalysisJob, PrivacySetting
from ..schemas import AISummaryResponse, SummaryRegenerateRequest
from ..services.ai_analyzer import AIAnalyzer
from ..services.video_processor import VideoProcessor
import asyncio

router = APIRouter(prefix="/api/summaries", tags=["AI Summaries"])

@router.get("", response_model=List[AISummaryResponse])
def list_summaries(db: Session = Depends(get_db)):
    return db.query(AISummary).order_by(AISummary.id.desc()).all()

@router.get("/latest", response_model=AISummaryResponse)
def get_latest_summary(db: Session = Depends(get_db)):
    summary = db.query(AISummary).order_by(AISummary.id.desc()).first()
    if not summary:
        raise HTTPException(status_code=404, detail="No summaries found")
    return summary

@router.get("/{summary_id}", response_model=AISummaryResponse)
def get_summary(summary_id: int, db: Session = Depends(get_db)):
    summary = db.query(AISummary).filter(AISummary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    return summary

@router.post("/regenerate", response_model=AISummaryResponse)
async def regenerate_summary(payload: SummaryRegenerateRequest, db: Session = Depends(get_db)):
    video = None
    if payload.video_id:
        video = db.query(Video).filter(Video.id == payload.video_id).first()
    if not video:
        video = db.query(Video).filter(Video.status == "completed").order_by(Video.id.desc()).first()

    if not video:
        raise HTTPException(status_code=404, detail="No completed video found to regenerate summary for.")

    privacy = db.query(PrivacySetting).first()
    blur_faces = privacy.blur_faces if privacy else False
    local_processing_only = privacy.local_processing_only if privacy else False

    meta = VideoProcessor.extract_metadata(video.file_path)
    sampled = VideoProcessor.sample_frames_and_detect_motion(
        video.id,
        video.file_path,
        sample_interval_sec=1.0,
        blur_faces=blur_faces
    )
    
    try:
        events_data, summary_data, model_name = await AIAnalyzer.analyze_video_frames(
            video_metadata=meta,
            sampled_frames=sampled,
            is_demo=video.is_demo,
            local_processing_only=local_processing_only,
            blur_faces=blur_faces
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI Vision Analysis failed: {str(e)}") from e

    summary = db.query(AISummary).filter(AISummary.video_id == video.id).first()
    if not summary:
        summary = AISummary(video_id=video.id)
        db.add(summary)

    summary.overall_summary = summary_data.get("overall_summary", "Refreshed summary.")
    summary.observations = summary_data.get("observations", "")
    summary.evidence = summary_data.get("evidence", "")
    summary.unknowns = summary_data.get("unknowns", "")
    summary.uncertainty_limitations = summary_data.get("uncertainty_limitations", summary_data.get("unknowns", ""))
    summary.review_rationale = summary_data.get("review_rationale", "")
    summary.suggested_action = summary_data.get("suggested_action", "")
    summary.model_used = model_name
    summary.objects_detected = summary_data.get("objects_detected", "Person, Door")
    summary.frames_sampled = summary_data.get("frames_sampled", len(sampled))
    summary.status = "Analyzed"

    db.commit()
    db.refresh(summary)
    return summary

@router.get("/{summary_id}/export")
def export_summary(
    summary_id: int,
    format: Literal["markdown", "json", "text"] = Query("markdown"),
    db: Session = Depends(get_db)
):
    summary = db.query(AISummary).filter(AISummary.id == summary_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    if format == "json":
        return {
            "id": summary.id,
            "overall_summary": summary.overall_summary,
            "observations": summary.observations,
            "time_range": summary.time_range,
            "evidence": summary.evidence,
            "unknowns": summary.unknowns,
            "review_rationale": summary.review_rationale,
            "suggested_action": summary.suggested_action,
            "model_used": summary.model_used,
            "created_at": summary.created_at.isoformat()
        }

    md_report = f"""# SafeHome AI — Security Intelligence Report
**Generated:** {summary.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Analysis Model:** {summary.model_used}  
**Time Range:** {summary.time_range}  
**Objects Identified:** {summary.objects_detected}  

---

### Executive AI Summary
{summary.overall_summary}

### Review Recommendation
**Rationale:** {summary.review_rationale}  
**Suggested Next Step:** {summary.suggested_action}  

### Verified Observations
{summary.observations}

### Visual Evidence Grounding
{summary.evidence}

### Unknown / Unverified Information
{summary.unknowns}

---
*Notice: SafeHome AI enforces strict visual grounding. This report contains no inferred intent or unverified accusations.*
"""
    ext = "txt" if format == "text" else "md"
    return {"content": md_report, "filename": f"SafeHome_Report_{summary.id}.{ext}"}
