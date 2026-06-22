import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
import app.models.agent_registry
from app.integration.registry import AgentRegistry
from app.integration.native_provider import NativeProvider
from app.integration.mock_provider import MockProvider


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


registry = AgentRegistry()


class TestAgentRegistry:
    def test_auto_discover(self, db_session):
        count = registry.auto_discover(
            db_session, [NativeProvider(), MockProvider()]
        )
        assert count == 7
        entries = registry.list_all(db_session)
        assert len(entries) == 7
        for e in entries:
            assert e.status == "discovered"

    def test_register_manual(self, db_session):
        entry = registry.register_manual(
            db_session,
            provider="test",
            name="Custom Agent",
            description="A test agent",
            capabilities=["python", "api"],
        )
        assert entry.id is not None
        assert entry.status == "pending"
        assert entry.name == "Custom Agent"
        assert entry.provider == "test"

    def test_register_duplicate_raises(self, db_session):
        registry.register_manual(
            db_session,
            provider="test",
            name="Custom Agent",
            description="First registration",
            capabilities=["python"],
        )
        with pytest.raises(ValueError):
            registry.register_manual(
                db_session,
                provider="test",
                name="Custom Agent",
                description="Duplicate",
                capabilities=["python"],
            )

    def test_approve(self, db_session):
        entry = registry.register_manual(
            db_session,
            provider="test",
            name="Approve Me",
            description="Test approval",
            capabilities=["python"],
        )
        approved = registry.approve(db_session, entry.id)
        assert approved is not None
        assert approved.status == "approved"
        assert approved.id == entry.id

    def test_reject(self, db_session):
        entry = registry.register_manual(
            db_session,
            provider="test",
            name="Reject Me",
            description="Test rejection",
            capabilities=["python"],
        )
        rejected = registry.reject(db_session, entry.id)
        assert rejected is not None
        assert rejected.status == "rejected"
        assert rejected.id == entry.id

    def test_search_by_capability(self, db_session):
        a1 = registry.register_manual(
            db_session,
            provider="test",
            name="Py Agent",
            description="Python agent",
            capabilities=["python", "api"],
        )
        registry.approve(db_session, a1.id)

        a2 = registry.register_manual(
            db_session,
            provider="test",
            name="Front Agent",
            description="Frontend agent",
            capabilities=["frontend", "css"],
        )
        registry.approve(db_session, a2.id)

        results = registry.search_by_capability(db_session, ["python"])
        assert len(results) == 1
        assert results[0].id == a1.id

        results = registry.search_by_capability(db_session, ["java"])
        assert len(results) == 0

    def test_list_all(self, db_session):
        e1 = registry.register_manual(
            db_session,
            provider="test",
            name="Alpha",
            description="Will be pending",
            capabilities=["a"],
        )
        e2 = registry.register_manual(
            db_session,
            provider="test",
            name="Beta",
            description="Will be rejected",
            capabilities=["b"],
        )
        registry.reject(db_session, e2.id)
        e3 = registry.register_manual(
            db_session,
            provider="test",
            name="Gamma",
            description="Will be rejected too",
            capabilities=["c"],
        )
        registry.reject(db_session, e3.id)

        all_entries = registry.list_all(db_session)
        assert len(all_entries) == 3

        pending = registry.list_all(db_session, status="pending")
        assert len(pending) == 1

        approved = registry.list_all(db_session, status="approved")
        assert len(approved) == 0

    def test_get_by_id(self, db_session):
        entry = registry.register_manual(
            db_session,
            provider="test",
            name="Find Me",
            description="Lookup test",
            capabilities=["x"],
        )
        found = registry.get_by_id(db_session, entry.id)
        assert found is not None
        assert found.id == entry.id

        not_found = registry.get_by_id(db_session, 99999)
        assert not_found is None
