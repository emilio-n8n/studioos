import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models.event_log  # noqa: F401 — register model
from app.kernel.event_store import event_store


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


def test_append(db_session):
    entry = event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload={"name": "test"})
    assert entry.id is not None
    assert entry.sequence == 1
    assert entry.event_type == "PROJECT_CREATED"
    assert entry.payload == {"name": "test"}


def test_append_multiple(db_session):
    event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload={"name": "test"})
    event_store.append(db_session, project_id=1, event_type="STRATEGY_GENERATED", payload={"strategy": "plan_a"})
    e3 = event_store.append(db_session, project_id=1, event_type="AGENT_SPAWNED", payload={"agent": "alice"})
    assert e3.sequence == 3


def test_replay(db_session):
    p1 = {"name": "p1"}
    p2 = {"name": "p2"}
    p3 = {"name": "p3"}
    event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload=p1)
    event_store.append(db_session, project_id=1, event_type="STRATEGY_GENERATED", payload=p2)
    event_store.append(db_session, project_id=1, event_type="AGENT_SPAWNED", payload=p3)

    events = event_store.replay(db_session, project_id=1)
    assert len(events) == 3
    assert events[0].payload == p1
    assert events[1].payload == p2
    assert events[2].payload == p3


def test_replay_since(db_session):
    event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload={"name": "a"})
    e2 = event_store.append(db_session, project_id=1, event_type="STRATEGY_GENERATED", payload={"name": "b"})
    event_store.append(db_session, project_id=1, event_type="AGENT_SPAWNED", payload={"name": "c"})

    events = event_store.replay(db_session, project_id=1, since_id=e2.id)
    assert len(events) == 1
    assert events[0].payload == {"name": "c"}


def test_replay_by_type(db_session):
    event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload={"name": "x"})
    event_store.append(db_session, project_id=1, event_type="STRATEGY_GENERATED", payload={"strat": "y"})
    event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload={"name": "z"})

    events = event_store.replay_by_type(db_session, project_id=1, event_type="PROJECT_CREATED")
    assert len(events) == 2
    assert all(e.event_type == "PROJECT_CREATED" for e in events)


def test_count(db_session):
    assert event_store.count(db_session, project_id=1) == 0
    event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload={})
    event_store.append(db_session, project_id=1, event_type="STRATEGY_GENERATED", payload={})
    event_store.append(db_session, project_id=1, event_type="AGENT_SPAWNED", payload={})
    assert event_store.count(db_session, project_id=1) == 3
