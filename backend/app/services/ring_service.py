import hmac
import hashlib
import datetime
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session
from ..config import settings
from ..models import RingDevice, Event, Notification

class RingService:
    AMAZON_VISION_BASE_URL = "https://api.amazonvision.com"

    @classmethod
    def verify_webhook_signature(cls, payload_body: bytes, signature_header: Optional[str]) -> bool:
        """
        Verifies Amazon Vision / Ring webhook HMAC-SHA256 signature (X-Ring-Signature).
        If no secret is configured (or in simulator mode), allows verification with a logged note.
        """
        if not settings.RING_WEBHOOK_SECRET:
            # When in simulator/demo mode or during initial local setup
            return True

        if not signature_header:
            return False

        expected_sig = hmac.new(
            settings.RING_WEBHOOK_SECRET.encode(),
            payload_body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, signature_header)

    @classmethod
    async def get_partner_devices(cls, access_token: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Queries Amazon Vision Partner API (GET /devices) adhering to JSON:API specification.
        Falls back to registered database devices or simulator state if credentials are not configured.
        """
        if access_token and not settings.RING_SIMULATOR_MODE:
            try:
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.api+json",
                    "Content-Type": "application/vnd.api+json"
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(f"{cls.AMAZON_VISION_BASE_URL}/v1/devices", headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        # Parse JSON:API format
                        devices = []
                        for item in data.get("data", []):
                            attrs = item.get("attributes", {})
                            devices.append({
                                "device_id": item.get("id"),
                                "name": attrs.get("description", "Ring Device"),
                                "device_type": attrs.get("kind", "doorbell"),
                                "location": attrs.get("location_name", "Front Entrance"),
                                "status": "online" if attrs.get("online") else "offline",
                                "battery_level": attrs.get("battery_life", 100),
                                "firmware_version": attrs.get("firmware_version", "v4.0.0"),
                                "is_simulator": False
                            })
                        return devices
            except Exception as e:
                print(f"[RingService] Failed to query live Amazon Vision API: {e}")

        # Return registered simulator devices
        return [
            {
                "device_id": "ring-doorbell-pro-01",
                "name": "Front Door Video Doorbell Pro",
                "device_type": "doorbell",
                "location": "Front Door",
                "status": "online",
                "battery_level": 92,
                "firmware_version": "v4.2.1-amazon",
                "is_simulator": True
            },
            {
                "device_id": "ring-floodlight-cam-02",
                "name": "Driveway Floodlight Cam",
                "device_type": "floodlight",
                "location": "Driveway",
                "status": "online",
                "battery_level": 100, # Hardwired
                "firmware_version": "v3.8.9-amazon",
                "is_simulator": True
            },
            {
                "device_id": "ring-stickup-cam-03",
                "name": "Backyard Stick Up Cam",
                "device_type": "camera",
                "location": "Backyard Patio",
                "status": "online",
                "battery_level": 74,
                "firmware_version": "v4.1.0-amazon",
                "is_simulator": True
            }
        ]

    @classmethod
    def ingest_webhook_event(
        cls,
        db: Session,
        payload: Dict[str, Any],
        is_simulator: bool = False
    ) -> Event:
        """
        Normalizes Amazon Vision / Ring webhook events into the unified SafeHome Event schema.
        Handles event types: 'motion', 'ding', 'person', 'package_delivered'.
        Simulator events are isolated (source_type='test_fixture', is_demo=True)
        and NEVER create notifications in the production user notification center.
        """
        event_type = payload.get("event_type") or payload.get("type", "motion")
        device_id = payload.get("device_id", "ring-doorbell-pro-01")
        location = payload.get("location", "Front Door")
        now = datetime.datetime.utcnow()

        if event_type == "ding":
            title = "Doorbell ring detected"
            category = "Person"
            description = f"Ring Video Doorbell button pressed at {location}."
            priority = "Medium"
            priority_reason = "Visitor at the entrance door requiring homeowner attention."
        elif event_type == "package_delivered":
            title = "Package delivery detected"
            category = "Package"
            description = f"Package detected on porch near {location}."
            priority = "Low"
            priority_reason = "Package delivery confirmation; parcel left at entrance."
        elif event_type == "person":
            title = "Person detected near entrance"
            category = "Person"
            description = f"Person presence detected by Ring camera at {location}."
            priority = "Medium"
            priority_reason = "Human presence detected in monitored perimeter zone."
        else: # motion
            title = "Motion activity detected"
            category = "Motion"
            description = f"Motion sensor triggered on {device_id} at {location}."
            priority = "Low"
            priority_reason = "General motion detection within configured motion zone."

        if is_simulator:
            source = "simulator"
            source_type = "test_fixture"
            title_prefix = "[Simulated] "
            raw_evidence = f"[Sandbox Simulation] Dispatched via Ring Simulator ({event_type}) on device {device_id}."
            dedup_key = f"sim_{device_id}_{event_type}_{int(now.timestamp())}"
        else:
            source = "ring_integration"
            source_type = "ring_integration"
            title_prefix = ""
            raw_evidence = f"Ingested from verified Amazon Vision API Webhook ({event_type}) on device {device_id}."
            dedup_key = f"ring_{device_id}_{payload.get('event_id', int(now.timestamp()))}"

        event = Event(
            source=source,
            source_type=source_type,
            category=category,
            title=f"{title_prefix}{title}",
            description=description,
            start_time="00:00",
            end_time="00:15",
            start_seconds=0.0,
            end_seconds=15.0,
            timestamp=now,
            priority=priority,
            priority_reason=priority_reason,
            review_status="Pending Review",
            location=location,
            confidence=0.96,
            raw_evidence=raw_evidence,
            is_demo=is_simulator,
            dedup_key=dedup_key
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        # Only genuine non-simulator partner webhook events create in-app notifications
        if not is_simulator:
            notif_dedup = f"notif_ring_{event.id}"
            if not db.query(Notification).filter(Notification.dedup_key == notif_dedup).first():
                notification = Notification(
                    event_id=event.id,
                    notification_type="ring_integration",
                    title=f"Ring Alert: {title}",
                    message=description,
                    priority=priority,
                    is_read=False,
                    is_resolved=False,
                    created_at=now,
                    dedup_key=notif_dedup
                )
                db.add(notification)
                db.commit()

        return event
