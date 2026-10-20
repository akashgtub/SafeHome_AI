import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Video, Event, AISummary, RingDevice, AnalysisJob
from ..config import settings
from ..schemas import DashboardStatsResponse, EventResponse, VideoResponse, AISummaryResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Genuine non-demo event metrics
    total_events = db.query(Event).filter(Event.is_demo == False).count()
    review_pending = db.query(Event).filter(Event.is_demo == False, Event.review_status == "Pending Review").count()
    
    total_videos = db.query(Video).filter(Video.is_demo == False).count()
    completed_videos = db.query(Video).filter(Video.is_demo == False, Video.status == "completed").count()
    ai_summarized_count = db.query(AISummary).filter(AISummary.is_demo == False).count()
    ai_percentage = int((completed_videos / total_videos * 100)) if total_videos > 0 else 0

    # Genuine physical online devices (exclude test simulator fixtures)
    connected_devices = db.query(RingDevice).filter(
        RingDevice.is_simulator == False,
        RingDevice.status == "online"
    ).count()
    device_subtitle = "Connected (Live)" if connected_devices > 0 else "Not connected"

    # Events this week vs previous week calculation
    today = datetime.date.today()
    this_week_start = datetime.datetime.combine(today - datetime.timedelta(days=7), datetime.time.min)
    prev_week_start = datetime.datetime.combine(today - datetime.timedelta(days=14), datetime.time.min)
    events_this_week = db.query(Event).filter(Event.is_demo == False, Event.timestamp >= this_week_start).count()
    events_prev_week = db.query(Event).filter(Event.is_demo == False, Event.timestamp >= prev_week_start, Event.timestamp < this_week_start).count()
    
    if events_prev_week > 0:
        pct = int(((events_this_week - events_prev_week) / events_prev_week) * 100)
        events_this_week_change = f"{'+' if pct >= 0 else ''}{pct}% vs last week"
    elif events_this_week > 0:
        events_this_week_change = f"{events_this_week} this week"
    else:
        events_this_week_change = "0 this week"

    # Latest genuine video (shows completed, processing, or failed status accurately)
    active_video_model = db.query(Video).filter(
        Video.is_demo == False
    ).order_by(Video.id.desc()).first()

    active_video = None
    if active_video_model:
        active_video = VideoResponse.model_validate(active_video_model)
        active_video.stream_url = f"/api/videos/stream/{active_video_model.id}"

    # Latest genuine summary (only exists if analysis completed successfully)
    active_summary_model = None
    if active_video_model and active_video_model.status == "completed":
        active_summary_model = db.query(AISummary).filter(
            AISummary.video_id == active_video_model.id,
            AISummary.is_demo == False
        ).first()

    active_summary = AISummaryResponse.model_validate(active_summary_model) if active_summary_model else None

    # Video Analysis Details
    analysis_details = None
    if active_video_model:
        job = db.query(AnalysisJob).filter(AnalysisJob.video_id == active_video_model.id).first()
        mins = int(active_video_model.duration // 60)
        secs = int(active_video_model.duration % 60)
        duration_str = f"{mins:02d}:{secs:02d}"

        frames_analyzed = job.frames_analyzed if (job and job.frames_analyzed is not None) else 0
        model_name = (job.model_used if job else None) or (active_summary_model.model_used if active_summary_model else settings.AI_PROVIDER)
        
        objects_str = active_summary_model.objects_detected if (active_summary_model and active_summary_model.objects_detected) else "None detected"
        processed_at_str = active_video_model.created_at.strftime("%b %d, %Y %I:%M %p")

        if active_summary_model and "Local" in active_summary_model.model_used:
            analysis_mode = "Local Edge CV (Privacy Mode)"
        elif "gemini" in model_name.lower():
            analysis_mode = f"Gemini Cloud Vision ({settings.GEMINI_MODEL})"
        elif "openai" in model_name.lower():
            analysis_mode = f"OpenAI Cloud Vision ({settings.OPENAI_MODEL})"
        else:
            analysis_mode = "Edge Motion Analysis"

        analysis_details = {
            "video_duration": duration_str,
            "frames_analyzed": f"{frames_analyzed} frames",
            "frames_sampled": frames_analyzed,
            "objects_detected": objects_str,
            "analysis_model": model_name,
            "analysis_mode": analysis_mode,
            "analysis_status": active_video_model.status,
            "processed_at": processed_at_str,
            "error_message": active_video_model.error_message
        }

    # Recent detected events (ordered by timestamp or video time)
    recent_events_models = db.query(Event).filter(Event.is_demo == False).order_by(Event.id.desc()).limit(10).all()
    recent_events = [EventResponse.model_validate(e) for e in recent_events_models]

    # Priority distribution
    low_count = db.query(Event).filter(Event.is_demo == False, Event.priority == "Low").count()
    med_count = db.query(Event).filter(Event.is_demo == False, Event.priority == "Medium").count()
    high_count = db.query(Event).filter(Event.is_demo == False, Event.priority == "High").count()
    priority_distribution = {"Low": low_count, "Medium": med_count, "High": high_count}

    # Category distribution
    categories = db.query(Event.category, func.count(Event.id)).filter(Event.is_demo == False).group_by(Event.category).all()
    category_distribution = {cat: count for cat, count in categories}

    # Weekly trend (last 7 days) — strictly database-driven without fabricated counts
    weekly_trend = []
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for i in range(6, -1, -1):
        target_date = today - datetime.timedelta(days=i)
        day_label = days[target_date.weekday()]
        start_dt = datetime.datetime.combine(target_date, datetime.time.min)
        end_dt = datetime.datetime.combine(target_date, datetime.time.max)
        count = db.query(Event).filter(Event.is_demo == False, Event.timestamp >= start_dt, Event.timestamp <= end_dt).count()
        weekly_trend.append({"day": day_label, "date": target_date.strftime("%b %d"), "events": count})

    return {
        "total_events": total_events,
        "events_this_week_change": events_this_week_change,
        "review_pending": review_pending,
        "review_pending_subtitle": f"{review_pending} need attention" if review_pending > 0 else "All caught up",
        "ai_summarized_count": ai_summarized_count,
        "ai_summarized_percentage": ai_percentage,
        "connected_devices_count": connected_devices,
        "connected_devices_subtitle": device_subtitle,
        "recent_events": recent_events,
        "active_video": active_video,
        "active_summary": active_summary,
        "analysis_details": analysis_details,
        "priority_distribution": priority_distribution,
        "category_distribution": category_distribution,
        "weekly_trend": weekly_trend
    }
