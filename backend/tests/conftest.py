import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure sys.path includes both repository root and backend directory
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from backend.app.main import app
    from backend.app.database import Base, get_db
    import backend.app.database as db_module
    from backend.app.models import PrivacySetting
    from backend.app.config import settings
except ImportError:
    from app.main import app
    from app.database import Base, get_db
    import app.database as db_module
    from app.models import PrivacySetting
    from app.config import settings

TEST_DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "test_safehome.db"))
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE.replace(os.sep, '/')}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Redirect backend database sessionmaker and engine for test isolation
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture(autouse=True)
def clean_test_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.add(PrivacySetting(retention_days=30, auto_delete=False, blur_faces=False, local_processing_only=False))
        db.commit()
    finally:
        db.close()
    yield

@pytest.fixture(autouse=True)
def isolate_test_storage(monkeypatch, tmp_path):
    test_upload = str(tmp_path / "test_uploads")
    test_frames = str(tmp_path / "test_frames")
    os.makedirs(test_upload, exist_ok=True)
    os.makedirs(test_frames, exist_ok=True)
    monkeypatch.setattr(settings, "UPLOAD_DIR", test_upload)
    monkeypatch.setattr(settings, "FRAMES_DIR", test_frames)

