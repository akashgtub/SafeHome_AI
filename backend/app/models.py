import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True, nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, default=0) # bytes
    duration = Column(Float, default=0.0) # seconds
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    fps = Column(Float, default=0.0)
    status = Column(String(50), default="pending") # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_demo = Column(Boolean, default=False)
    retention_expires_at = Column(DateTime, nullable=True)

    analysis_jobs = relationship("AnalysisJob", back_populates="video", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="video", cascade="all, delete-orphan")
    summaries = relationship("AISummary", back_populates="video", cascade="all, delete-orphan")

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="queued") # queued, running, completed, failed
    progress = Column(Integer, default=0) # 0 to 100
    frames_analyzed = Column(Integer, default=0)
    model_used = Column(String(100), default="mock")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)

    video = relationship("Video", back_populates="analysis_jobs")

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id", ondelete="SET NULL"), nullable=True)
    source = Column(String(50), default="uploaded_video") # uploaded_video, ring_integration, simulator
    source_type = Column(String(50), default="video_upload") # video_upload, ring_integration, test_fixture
    category = Column(String(50), nullable=False) # Person, Vehicle, Animal, Package, Motion, Door
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    start_time = Column(String(20), default="00:00") # "00:04"
    end_time = Column(String(20), default="00:00") # "00:11"
    start_seconds = Column(Float, default=0.0)
    end_seconds = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    thumbnail_path = Column(String(512), nullable=True)
    priority = Column(String(20), default="Low") # Low, Medium, High
    priority_reason = Column(Text, nullable=True)
    review_status = Column(String(50), default="Pending Review") # Pending Review, Reviewed, Acknowledged, Dismissed
    location = Column(String(100), default="Front Door")
    confidence = Column(Float, default=0.9)
    raw_evidence = Column(Text, nullable=True) # JSON or descriptive observations
    uncertainty = Column(Text, nullable=True) # visual uncertainty notes
    detection_mode = Column(String(50), default="AI Visual Analysis") # "Local Motion Analysis", "AI Visual Analysis", "Ring Integration Event"
    is_demo = Column(Boolean, default=False)
    dedup_key = Column(String(128), unique=True, nullable=True, index=True)

    video = relationship("Video", back_populates="events")
    reviews = relationship("ReviewRecord", back_populates="event", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="event", cascade="all, delete-orphan")

class AISummary(Base):
    __tablename__ = "ai_summaries"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    overall_summary = Column(Text, nullable=False)
    observations = Column(Text, nullable=True)
    time_range = Column(String(50), default="00:00 - 00:20")
    evidence = Column(Text, nullable=True)
    unknowns = Column(Text, nullable=True)
    uncertainty_limitations = Column(Text, nullable=True)
    review_rationale = Column(Text, nullable=True)
    suggested_action = Column(Text, nullable=True)
    status = Column(String(50), default="Analyzed") # Analyzed, Pending, Needs Review
    model_used = Column(String(100), default="Vision AI (Local)")
    objects_detected = Column(String(255), default="Person, Door")
    frames_sampled = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_demo = Column(Boolean, default=False)

    video = relationship("Video", back_populates="summaries")

class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False) # marked_reviewed, marked_unreviewed, acknowledged, dismissed
    notes = Column(Text, nullable=True)
    reviewed_by = Column(String(100), default="Akash T (Home Owner)")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    event = relationship("Event", back_populates="reviews")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    job_id = Column(Integer, ForeignKey("analysis_jobs.id", ondelete="SET NULL"), nullable=True)
    notification_type = Column(String(50), default="system") # video_upload, analysis, security_event, ring_integration
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), default="Low") # Low, Medium, High
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    dedup_key = Column(String(128), unique=True, nullable=True, index=True)

    event = relationship("Event", back_populates="notifications")

class RingDevice(Base):
    __tablename__ = "ring_devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    device_type = Column(String(50), default="doorbell") # doorbell, floodlight, stickup_cam, chime
    location = Column(String(100), default="Front Door")
    status = Column(String(50), default="online") # online, offline, streaming
    battery_level = Column(Integer, default=88) # percentage
    firmware_version = Column(String(50), default="v4.2.1-amazon")
    last_sync_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_simulator = Column(Boolean, default=True)
    source_type = Column(String(50), default="ring_partner") # ring_partner, test_fixture

class PrivacySetting(Base):
    __tablename__ = "privacy_settings"

    id = Column(Integer, primary_key=True, index=True)
    retention_days = Column(Integer, default=30)
    auto_delete = Column(Boolean, default=False)
    blur_faces = Column(Boolean, default=False)
    local_processing_only = Column(Boolean, default=False)
    allow_cloud_vision = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
