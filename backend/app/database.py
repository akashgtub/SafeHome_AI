from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from . import models
    Base.metadata.create_all(bind=engine)

    # Safe schema migration for SQLite to ensure new columns exist on pre-existing databases
    try:
        with engine.connect() as conn:
            cursor = conn.connection.cursor()
            
            events_cols = [r[1] for r in cursor.execute("PRAGMA table_info(events)").fetchall()]
            if events_cols:
                if "job_id" not in events_cols:
                    cursor.execute("ALTER TABLE events ADD COLUMN job_id INTEGER")
                if "source_type" not in events_cols:
                    cursor.execute("ALTER TABLE events ADD COLUMN source_type VARCHAR DEFAULT 'video_upload'")
                if "dedup_key" not in events_cols:
                    cursor.execute("ALTER TABLE events ADD COLUMN dedup_key VARCHAR")
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_events_dedup_key ON events(dedup_key)")

            notifs_cols = [r[1] for r in cursor.execute("PRAGMA table_info(notifications)").fetchall()]
            if notifs_cols:
                if "video_id" not in notifs_cols:
                    cursor.execute("ALTER TABLE notifications ADD COLUMN video_id INTEGER")
                if "job_id" not in notifs_cols:
                    cursor.execute("ALTER TABLE notifications ADD COLUMN job_id INTEGER")
                if "notification_type" not in notifs_cols:
                    cursor.execute("ALTER TABLE notifications ADD COLUMN notification_type VARCHAR DEFAULT 'system'")
                if "dedup_key" not in notifs_cols:
                    cursor.execute("ALTER TABLE notifications ADD COLUMN dedup_key VARCHAR")
                    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_notifications_dedup_key ON notifications(dedup_key)")

            devices_cols = [r[1] for r in cursor.execute("PRAGMA table_info(ring_devices)").fetchall()]
            if devices_cols:
                if "source_type" not in devices_cols:
                    cursor.execute("ALTER TABLE ring_devices ADD COLUMN source_type VARCHAR DEFAULT 'ring_partner'")
            
            conn.connection.commit()
    except Exception as e:
        print(f"Warning during init_db schema migration: {e}")
