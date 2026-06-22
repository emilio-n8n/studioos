import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
import app.models.agent_registry  # noqa: F401
from app.integration.registry import AgentRegistry
from app.integration.native_provider import NativeProvider
from app.integration.mock_provider import MockProvider
from app.integration.dispatcher import TaskDispatcher


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


@pytest.fixture
def registry():
    return AgentRegistry()


@pytest.fixture
def providers():
    return [NativeProvider(), MockProvider(delay=0.1)]


@pytest.fixture
def dispatcher(registry, providers):
    return TaskDispatcher(registry, providers)


def _register_and_approve_backend(db, registry):
    entry = registry.register_manual(
        db,
        provider="mock",
        name="Backend Developer (Mock)",
        description="Builds APIs, models, and database logic",
        capabilities=["backend", "python", "api", "database"],
        cost=6, speed=7, quality=8,
    )
    registry.approve(db, entry.id)


def _register_and_approve_all_mock(db, registry):
    _register_and_approve_backend(db, registry)
    entry2 = registry.register_manual(
        db,
        provider="mock",
        name="Frontend Developer (Mock)",
        description="Creates UI components and responsive layouts",
        capabilities=["frontend", "typescript", "css", "ui"],
        cost=5, speed=8, quality=7,
    )
    registry.approve(db, entry2.id)


@pytest.mark.asyncio
async def test_dispatch_task_no_match(db_session, dispatcher):
    task = {"id": 1, "title": "Quantum computing research", "description": "Research quantum algorithms"}
    context = {"project_id": 1, "project_name": "Test"}
    result = await dispatcher.dispatch_task(task, context, db_session)
    assert result.status == "completed"
    assert "executor" in result.output.get("message", "")


@pytest.mark.asyncio
async def test_dispatch_task_with_match(db_session, registry, dispatcher):
    _register_and_approve_backend(db_session, registry)

    task = {"id": 2, "title": "Build API endpoint", "description": "Create a Python backend API with database integration"}
    context = {"project_id": 1, "project_name": "Test"}
    result = await dispatcher.dispatch_task(task, context, db_session)
    assert result.status == "completed"
    assert "backend_dev" in result.output.get("message", "")


@pytest.mark.asyncio
async def test_dispatch_batch(db_session, registry, dispatcher):
    _register_and_approve_all_mock(db_session, registry)

    tasks = [
        {"id": 3, "title": "Backend API task", "description": "Python database integration"},
        {"id": 4, "title": "Frontend UI task", "description": "React CSS layout design"},
    ]
    context = {"project_id": 1, "project_name": "Test"}
    results = await dispatcher.dispatch_batch(tasks, context, db_session)
    assert len(results) == 2
    for r in results:
        assert r.status == "completed"


@pytest.mark.asyncio
async def test_fallback_when_no_match(db_session, dispatcher):
    task = {"id": 5, "title": "Unknown task", "description": "nonexistent_super_skill required"}
    context = {"project_id": 1, "project_name": "Test"}
    result = await dispatcher.dispatch_task(task, context, db_session)
    assert result.status == "completed"
    assert "executor" in result.output.get("message", "")
