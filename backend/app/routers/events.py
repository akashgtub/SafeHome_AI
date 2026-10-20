from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..models import Event, ReviewRecord
from ..schemas import EventResponse, EventReviewUpdate
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("", response_model=List[EventResponse])
def get_events(
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    video_id: Optional[int] = Query(None),
    include_demo: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    if not include_demo:
        query = query.filter(Event.is_demo == False)

    if category and category.lower() != "all":
        query = query.filter(Event.category.ilike(f"%{category}%"))
    if priority and priority.lower() != "all":
        query = query.filter(Event.priority == priority)
    if review_status and review_status.lower() != "all":
        query = query.filter(Event.review_status == review_status)
    if source and source.lower() != "all":
        query = query.filter(Event.source == source)
    if video_id:
        query = query.filter(Event.video_id == video_id)
    if search:
        search_filter = or_(
            Event.title.ilike(f"%{search}%"),
            Event.description.ilike(f"%{search}%"),
            Event.location.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    events = query.order_by(Event.id.desc()).offset(offset).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.patch("/{event_id}/review", response_model=EventResponse)
def update_event_review(
    event_id: int,
    payload: EventReviewUpdate,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    action_map = {
        "Reviewed": "marked_reviewed",
        "Pending Review": "marked_unreviewed",
        "Acknowledged": "acknowledged",
        "Dismissed": "dismissed"
    }
    action = action_map.get(payload.review_status, "marked_reviewed")

    NotificationService.record_review_action(
        db=db,
        event_id=event_id,
        action=action,
        notes=payload.notes,
        reviewed_by=payload.reviewed_by or "Akash T"
    )

    db.refresh(event)
    return event

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
    return {"message": "Event deleted successfully"}
