import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
import backend.app.database as db_module
from backend.app.models import PrivacySetting

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
