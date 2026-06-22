import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app

import app.models.project
import app.models.organization
import app.models.department
import app.models.role
import app.models.agent
import app.models.task
import app.models.event_log
import app.models.agent_registry
import app.models.memory
import app.models.memory_node
import app.models.review_model
import app.models.pull_request_model


@pytest.fixture(scope="function")
def engine():
    e = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=e)
    yield e
    Base.metadata.drop_all(bind=e)


@pytest.fixture(scope="function")
def db_session(engine):
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_project(db_session):
    project = app.models.project.Project(
        name="Test Project",
        description="A test project",
        status="ready",
        provider="demo",
        openai_api_key="demo",
    )
    db_session.add(project)
    db_session.flush()

    org = app.models.organization.Organization(
        project_id=project.id,
        name="Test Organization",
    )
    db_session.add(org)
    db_session.flush()

    dept1 = app.models.department.Department(
        organization_id=org.id,
        name="Design",
    )
    db_session.add(dept1)
    db_session.flush()

    dept2 = app.models.department.Department(
        organization_id=org.id,
        name="Engineering",
    )
    db_session.add(dept2)
    db_session.flush()

    role1 = app.models.role.Role(
        department_id=dept1.id,
        title="Director of Design",
        is_governance=True,
        level=3,
    )
    db_session.add(role1)
    db_session.flush()

    role2 = app.models.role.Role(
        department_id=dept1.id,
        title="Designer",
        is_governance=False,
        level=1,
    )
    db_session.add(role2)
    db_session.flush()

    role3 = app.models.role.Role(
        department_id=dept2.id,
        title="Engineer",
        is_governance=False,
        level=1,
    )
    db_session.add(role3)
    db_session.flush()

    agent1 = app.models.agent.Agent(
        role_id=role1.id,
        name="Director Agent",
        agent_type="execution",
        provider="native",
    )
    db_session.add(agent1)
    db_session.flush()

    agent2 = app.models.agent.Agent(
        role_id=role3.id,
        name="Engineer Agent",
        agent_type="execution",
        provider="native",
    )
    db_session.add(agent2)
    db_session.flush()

    task1 = app.models.task.Task(
        project_id=project.id,
        department_id=dept1.id,
        assigned_agent_id=agent1.id,
        title="Design Review",
        priority=2,
        depends_on=[],
    )
    db_session.add(task1)
    db_session.flush()

    task2 = app.models.task.Task(
        project_id=project.id,
        department_id=dept2.id,
        assigned_agent_id=agent2.id,
        title="Build Feature",
        priority=1,
        depends_on=[task1.id],
    )
    db_session.add(task2)
    db_session.flush()

    task3 = app.models.task.Task(
        project_id=project.id,
        department_id=dept2.id,
        assigned_agent_id=agent1.id,
        title="Deploy",
        priority=0,
        depends_on=[task2.id],
    )
    db_session.add(task3)
    db_session.flush()

    db_session.commit()

    return project.id
