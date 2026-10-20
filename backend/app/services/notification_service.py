import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from ..models import Notification, ReviewRecord, Event

class NotificationService:
    @staticmethod
    def create_notification(
        db: Session,
        title: str,
        message: str,
        priority: str = "Low",
        event_id: Optional[int] = None
    ) -> Notification:
        notif = Notification(
            event_id=event_id,
            title=title,
            message=message,
            priority=priority,
            is_read=False,
            is_resolved=False,
            created_at=datetime.datetime.utcnow()
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def record_review_action(
        db: Session,
        event_id: int,
        action: str, # "marked_reviewed", "marked_unreviewed", "acknowledged", "dismissed"
        notes: Optional[str] = None,
        reviewed_by: str = "Akash T"
    ) -> ReviewRecord:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise ValueError(f"Event with id {event_id} not found.")

        # Update event review status
        if action == "marked_reviewed":
            event.review_status = "Reviewed"
        elif action == "marked_unreviewed":
            event.review_status = "Pending Review"
        elif action == "acknowledged":
            event.review_status = "Acknowledged"
        elif action == "dismissed":
            event.review_status = "Dismissed"

        record = ReviewRecord(
            event_id=event_id,
            action=action,
            notes=notes,
            reviewed_by=reviewed_by,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(record)

        # Mark corresponding notifications as resolved if reviewed/dismissed
        if action in ["marked_reviewed", "dismissed"]:
            db.query(Notification).filter(Notification.event_id == event_id).update({"is_resolved": True, "is_read": True})

        db.commit()
        db.refresh(record)
        return record
