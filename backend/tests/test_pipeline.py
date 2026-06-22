import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.config import settings

import app.models.project  # noqa: F401
import app.models.organization  # noqa: F401
import app.models.department  # noqa: F401
import app.models.role  # noqa: F401
import app.models.agent  # noqa: F401
import app.models.task  # noqa: F401
import app.models.event_log  # noqa: F401
import app.models.agent_registry  # noqa: F401
import app.models.memory  # noqa: F401
import app.models.memory_node  # noqa: F401
import app.models.review_model  # noqa: F401
import app.models.pull_request_model  # noqa: F401


@pytest.fixture
def db_session():
    os.makedirs(settings.output_dir, exist_ok=True)
    f = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    f.close()
    db_path = f.name
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    os.unlink(db_path)


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_pipeline_full_run(client):
    payload = {
        "name": "Pipeline Test Project",
        "description": "A full end-to-end test of the pipeline with demo data",
        "openai_api_key": "demo",
        "provider": "openai",
    }
    resp = client.post("/api/projects", json=payload)
    assert resp.status_code == 201
    project = resp.json()
    project_id = project["id"]
    assert project_id is not None

    resp = client.post(f"/api/projects/{project_id}/pipeline/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["tasks_completed"] >= 0

    resp = client.get(f"/api/projects/{project_id}")
    assert resp.status_code == 200
    project = resp.json()
    assert project["status"] in ("completed", "completed_with_errors")
