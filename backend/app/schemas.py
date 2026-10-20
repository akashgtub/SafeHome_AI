from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base Config for Pydantic v2
base_model_config = ConfigDict(from_attributes=True, protected_namespaces=())

# Video Schemas
class VideoBase(BaseModel):
    model_config = base_model_config
    filename: str
    original_filename: str
    file_size: int
    duration: float
    width: int
    height: int
    fps: float
    status: str
    is_demo: bool = False

class VideoResponse(VideoBase):
    model_config = base_model_config
    id: int
    file_path: str
    stream_url: Optional[str] = None
    created_at: datetime
    error_message: Optional[str] = None

# Event Schemas
class EventBase(BaseModel):
    model_config = base_model_config
    category: str
    title: str
    description: str
    start_time: str
    end_time: str
    priority: str
    priority_reason: Optional[str] = None
    location: str = "Front Door"
    source: str = "uploaded_video"
    confidence: float = 0.9

class EventCreate(EventBase):
    video_id: Optional[int] = None
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    thumbnail_path: Optional[str] = None
    raw_evidence: Optional[str] = None
    is_demo: bool = False

class EventReviewUpdate(BaseModel):
    model_config = base_model_config
    review_status: str # "Reviewed", "Pending Review", "Acknowledged", "Dismissed"
    notes: Optional[str] = None
    reviewed_by: Optional[str] = "Akash T"

class EventResponse(EventBase):
    model_config = base_model_config
    id: int
    video_id: Optional[int] = None
    start_seconds: float
    end_seconds: float
    timestamp: datetime
    thumbnail_path: Optional[str] = None
    review_status: str
    raw_evidence: Optional[str] = None
    is_demo: bool

# AI Summary Schemas
class AISummaryBase(BaseModel):
    model_config = base_model_config
    overall_summary: str
    observations: Optional[str] = None
    time_range: str = "00:00 - 00:20"
    evidence: Optional[str] = None
    unknowns: Optional[str] = None
    review_rationale: Optional[str] = None
    suggested_action: Optional[str] = None
    status: str = "Analyzed"
    model_used: str = "Vision AI (Local)"
    objects_detected: str = "Person, Door"

class AISummaryResponse(AISummaryBase):
    model_config = base_model_config
    id: int
    video_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_demo: bool

class SummaryRegenerateRequest(BaseModel):
    model_config = base_model_config
    video_id: Optional[int] = None
    provider: Optional[str] = None # "gemini", "openai", "mock"

# Analysis Job Schemas
class AnalysisJobResponse(BaseModel):
    model_config = base_model_config
    id: int
    video_id: int
    status: str
    progress: int
    frames_analyzed: int
    model_used: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

# Notification Schemas
class NotificationResponse(BaseModel):
    model_config = base_model_config
    id: int
    event_id: Optional[int] = None
    title: str
    message: str
    priority: str
    is_read: bool
    is_resolved: bool
    created_at: datetime

# Ring Schemas
class RingDeviceResponse(BaseModel):
    model_config = base_model_config
    id: int
    device_id: str
    name: str
    device_type: str
    location: str
    status: str
    battery_level: int
    firmware_version: str
    last_sync_at: datetime
    is_simulator: bool

class RingSimulatorTrigger(BaseModel):
    model_config = base_model_config
    event_type: str = "motion" # "motion", "ding", "person", "package_delivered"
    location: str = "Front Door"
    device_id: Optional[str] = "ring-doorbell-pro-01"

class RingSyncStatus(BaseModel):
    model_config = base_model_config
    connected: bool
    device_count: int
    last_sync: Optional[datetime] = None
    simulator_active: bool
    message: str

# Privacy Schemas
class PrivacySettingBase(BaseModel):
    model_config = base_model_config
    retention_days: int = 30
    auto_delete: bool = False
    blur_faces: bool = False
    local_processing_only: bool = False
    allow_cloud_vision: bool = True

class PrivacySettingUpdate(BaseModel):
    model_config = base_model_config
    retention_days: Optional[int] = None
    auto_delete: Optional[bool] = None
    blur_faces: Optional[bool] = None
    local_processing_only: Optional[bool] = None
    allow_cloud_vision: Optional[bool] = None

class PrivacySettingResponse(PrivacySettingBase):
    model_config = base_model_config
    id: int
    created_at: datetime
    updated_at: datetime

# Dashboard Stats Schema
class DashboardStatsResponse(BaseModel):
    model_config = base_model_config
    total_events: int
    events_this_week_change: str
    review_pending: int
    review_pending_subtitle: str
    ai_summarized_count: int
    ai_summarized_percentage: int
    connected_devices_count: int
    connected_devices_subtitle: str
    recent_events: List[EventResponse]
    active_video: Optional[VideoResponse] = None
    active_summary: Optional[AISummaryResponse] = None
    analysis_details: Optional[Dict[str, Any]] = None
    priority_distribution: Dict[str, int]
    category_distribution: Dict[str, int]
    weekly_trend: List[Dict[str, Any]]
