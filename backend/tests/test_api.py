import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_db

client = TestClient(app)

def setup_module(module):
    init_db()

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

def test_dashboard_stats():
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "review_pending" in data
    assert "active_video" in data
    assert "priority_distribution" in data

def test_list_events():
    resp = client.get("/api/events")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)
    if len(events) > 0:
        first_event = events[0]
        assert "id" in first_event
        assert "priority" in first_event

def test_event_review_workflow():
    resp = client.get("/api/events")
    assert resp.status_code == 200
    events = resp.json()
    if len(events) > 0:
        event_id = events[0]["id"]
        # Mark as Reviewed
        patch_resp = client.patch(
            f"/api/events/{event_id}/review",
            json={"review_status": "Reviewed", "notes": "Verified by test suite"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["review_status"] == "Reviewed"

def test_ring_simulator_and_devices():
    # Test device listing
    dev_resp = client.get("/api/ring/devices")
    assert dev_resp.status_code == 200
    devices = dev_resp.json()
    assert len(devices) > 0

    # Test simulator trigger
    sim_resp = client.post(
        "/api/ring/simulate-event",
        json={"event_type": "ding", "location": "Front Door"}
    )
    assert sim_resp.status_code == 200
    event_data = sim_resp.json()
    assert event_data["source"] == "ring_integration"
    assert "Doorbell" in event_data["title"] or "ring" in event_data["title"]

def test_summary_and_export():
    resp = client.get("/api/summaries")
    assert resp.status_code == 200
    summaries = resp.json()
    if len(summaries) > 0:
        sum_id = summaries[0]["id"]
        exp_resp = client.get(f"/api/summaries/{sum_id}/export?format=json")
        assert exp_resp.status_code == 200
        assert "overall_summary" in exp_resp.json()
