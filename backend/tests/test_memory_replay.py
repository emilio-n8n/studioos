from datetime import datetime, timezone, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models.event_log  # noqa: F401 — register model
from app.models.event_log import EventLog
from app.kernel.event_store import event_store
from app.kernel.memory_replay import memory_replay


@pytest.fixture
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()


def test_get_snapshot_empty(db_session):
    snapshot = memory_replay.get_snapshot(db_session, project_id=1)
    assert snapshot["events_count"] == 0
    assert snapshot["project"] is None


def test_get_snapshot_with_events(db_session):
    event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload={"name": "MyProject"})
    event_store.append(
        db_session, project_id=1, event_type="STRATEGY_GENERATED", payload={"strategy": "plan_a"}
    )

    snapshot = memory_replay.get_snapshot(db_session, project_id=1)
    assert snapshot["events_count"] == 2
    assert snapshot["project"] == {"name": "MyProject"}
    assert snapshot["strategy"] == {"strategy": "plan_a"}


def test_get_snapshot_at(db_session):
    base = datetime.now(timezone.utc)
    e1 = EventLog(
        project_id=1, event_type="PROJECT_CREATED", payload={"name": "first"},
        timestamp=base, sequence=1,
    )
    e2 = EventLog(
        project_id=1, event_type="STRATEGY_GENERATED", payload={"strategy": "plan_b"},
        timestamp=base + timedelta(seconds=10), sequence=2,
    )
    e3 = EventLog(
        project_id=1, event_type="AGENT_SPAWNED", payload={"agent": "alice"},
        timestamp=base + timedelta(seconds=20), sequence=3,
    )
    db_session.add_all([e1, e2, e3])
    db_session.flush()

    snapshot = memory_replay.get_snapshot_at(db_session, project_id=1, timestamp=base + timedelta(seconds=15))
    assert snapshot["events_count"] == 2
    assert snapshot["project"] == {"name": "first"}
    assert snapshot["strategy"] == {"strategy": "plan_b"}
    assert snapshot["agents"] == []


def test_replay(db_session):
    event_store.append(db_session, project_id=1, event_type="PROJECT_CREATED", payload={"name": "proj"})
    event_store.append(db_session, project_id=1, event_type="STRATEGY_GENERATED", payload={"strat": "s1"})

    result = memory_replay.replay(db_session, project_id=1)
    assert len(result) == 2
    assert result[0]["sequence"] == 1
    assert result[0]["event_type"] == "PROJECT_CREATED"
    assert result[1]["sequence"] == 2
    assert result[1]["event_type"] == "STRATEGY_GENERATED"
