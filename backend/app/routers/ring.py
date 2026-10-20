import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import RingDevice, Event
from ..schemas import RingDeviceResponse, RingSimulatorTrigger, RingSyncStatus, EventResponse
from ..services.ring_service import RingService
from ..config import settings

router = APIRouter(prefix="/api/ring", tags=["Ring Integration"])

@router.get("/status", response_model=RingSyncStatus)
def get_ring_status(db: Session = Depends(get_db)):
    devices = db.query(RingDevice).all()
    last_device = db.query(RingDevice).order_by(RingDevice.last_sync_at.desc()).first()
    last_sync = last_device.last_sync_at if last_device else datetime.datetime.utcnow()

    is_sim = settings.RING_SIMULATOR_MODE or not bool(settings.RING_CLIENT_ID)

    return {
        "connected": True,
        "device_count": len(devices),
        "last_sync": last_sync,
        "simulator_active": is_sim,
        "message": "Connected via Amazon Vision Partner API (Sandbox / Simulator Mode)" if is_sim else "Connected to Amazon Vision Partner API (Live)"
    }

@router.get("/devices", response_model=List[RingDeviceResponse])
def get_ring_devices(db: Session = Depends(get_db)):
    devices = db.query(RingDevice).all()
    if not devices:
        # Seed default devices
        seed_devices = [
            RingDevice(
                device_id="ring-doorbell-pro-01",
                name="Front Door Video Doorbell Pro",
                device_type="doorbell",
                location="Front Door",
                status="online",
                battery_level=92,
                firmware_version="v4.2.1-amazon",
                last_sync_at=datetime.datetime.utcnow(),
                is_simulator=True
            ),
            RingDevice(
                device_id="ring-floodlight-cam-02",
                name="Driveway Floodlight Cam",
                device_type="floodlight",
                location="Driveway",
                status="online",
                battery_level=100,
                firmware_version="v3.8.9-amazon",
                last_sync_at=datetime.datetime.utcnow(),
                is_simulator=True
            ),
            RingDevice(
                device_id="ring-stickup-cam-03",
                name="Backyard Stick Up Cam",
                device_type="camera",
                location="Backyard Patio",
                status="online",
                battery_level=74,
                firmware_version="v4.1.0-amazon",
                last_sync_at=datetime.datetime.utcnow(),
                is_simulator=True
            )
        ]
        for d in seed_devices:
            db.add(d)
        db.commit()
        devices = db.query(RingDevice).all()
    return devices

@router.post("/sync")
async def sync_ring_devices(db: Session = Depends(get_db)):
    now = datetime.datetime.utcnow()
    devices = db.query(RingDevice).all()
    for d in devices:
        d.last_sync_at = now
    db.commit()
    return {"message": "Sync completed successfully", "devices_synced": len(devices), "timestamp": now.isoformat()}

@router.post("/webhook")
async def ring_webhook(
    request: Request,
    x_ring_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    body = await request.body()
    if not RingService.verify_webhook_signature(body, x_ring_signature):
        raise HTTPException(status_code=401, detail="Invalid HMAC webhook signature")

    payload = await request.json()
    event = RingService.ingest_webhook_event(db, payload)
    return {"status": "success", "event_id": event.id, "title": event.title}

@router.post("/simulate-event", response_model=EventResponse)
def simulate_ring_event(payload: RingSimulatorTrigger, db: Session = Depends(get_db)):
    """
    Hackathon simulator trigger to test real-time Ring webhook ingestion
    and AI safety processing without physical hardware.
    """
    event_data = {
        "event_type": payload.event_type,
        "device_id": payload.device_id or "ring-doorbell-pro-01",
        "location": payload.location or "Front Door"
    }
    event = RingService.ingest_webhook_event(db, event_data)
    return event

@router.get("/docs")
def get_ring_developer_docs():
    return {
        "portal_url": "https://developer.ring.com",
        "amazon_developer_url": "https://developer.amazon.com",
        "api_base_url": "https://api.amazonvision.com",
        "spec": "JSON:API Specification",
        "auth_flow": "OAuth 2.0 with One-Way Account Linking & HMAC-SHA256 Nonces",
        "capabilities": [
            {"id": "device_discovery", "name": "Device Discovery (GET /v1/devices)", "status": "Supported"},
            {"id": "webhooks", "name": "Event Notifications (HMAC SHA-256 Webhooks)", "status": "Supported"},
            {"id": "media_download", "name": "Cloud MP4 Media & JPEG Snapshots", "status": "Supported"},
            {"id": "webrtc_whep", "name": "Low-Latency Live Streaming (WebRTC / WHEP)", "status": "Supported in Live Partner Tier"}
        ],
        "setup_guide": [
            "1. Register a Partner Account at developer.ring.com and create an Amazon Vision application.",
            "2. Obtain your Client ID, Client Secret, and Webhook Signing Key.",
            "3. Register your SafeHome AI Webhook URL (e.g., https://your-domain/api/ring/webhook).",
            "4. Configure environment variables RING_CLIENT_ID, RING_CLIENT_SECRET, RING_WEBHOOK_SECRET in backend/.env.",
            "5. To test without physical cameras or pending partner approval, use the built-in Ring Sandbox Simulator provided below."
        ]
    }
