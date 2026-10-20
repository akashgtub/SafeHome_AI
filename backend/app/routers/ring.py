import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import RingDevice, Event
from ..schemas import RingDeviceResponse, RingSimulatorTrigger, RingSyncStatus, EventResponse
from ..services.ring_service import RingService
from ..config import settings

router = APIRouter(prefix="/api/ring", tags=["Ring Integration"])

@router.get("/status", response_model=RingSyncStatus)
def get_ring_status(db: Session = Depends(get_db)):
    # Genuine physical devices only
    real_devices = db.query(RingDevice).filter(RingDevice.is_simulator == False).all()
    device_count = len(real_devices)
    last_device = db.query(RingDevice).filter(RingDevice.is_simulator == False).order_by(RingDevice.last_sync_at.desc()).first()
    last_sync = last_device.last_sync_at if last_device else None

    # Connected is ONLY true if real client credentials exist AND real devices are configured
    has_credentials = bool(settings.RING_CLIENT_ID and settings.RING_CLIENT_ID.strip())
    is_connected = has_credentials and (device_count > 0)
    is_sim_active = bool(settings.RING_SIMULATOR_MODE)

    if is_connected:
        message = "Connected to Amazon Vision Partner API (Live)"
    elif is_sim_active:
        message = "Ring Integration not connected to live hardware (Sandbox Simulator available)"
    else:
        message = "Ring Integration not connected. Configure credentials in backend/.env to connect."

    return {
        "connected": is_connected,
        "device_count": device_count,
        "last_sync": last_sync,
        "simulator_active": is_sim_active,
        "message": message
    }

@router.get("/devices", response_model=List[RingDeviceResponse])
def get_ring_devices(
    include_simulator: bool = Query(False),
    db: Session = Depends(get_db)
):
    query = db.query(RingDevice)
    if not include_simulator:
        query = query.filter(RingDevice.is_simulator == False)
    return query.all()

@router.post("/sync")
async def sync_ring_devices(db: Session = Depends(get_db)):
    now = datetime.datetime.utcnow()
    devices = db.query(RingDevice).filter(RingDevice.is_simulator == False).all()
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
    event = RingService.ingest_webhook_event(db, payload, is_simulator=False)
    return {"status": "success", "event_id": event.id, "title": event.title}

@router.post("/simulate-event", response_model=EventResponse)
def simulate_ring_event(payload: RingSimulatorTrigger, db: Session = Depends(get_db)):
    """
    Simulator trigger to test Ring webhook ingestion
    and AI safety processing in isolated test/sandbox mode.
    """
    event_data = {
        "event_type": payload.event_type,
        "device_id": payload.device_id or "ring-doorbell-pro-01",
        "location": payload.location or "Front Door"
    }
    event = RingService.ingest_webhook_event(db, event_data, is_simulator=True)
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
