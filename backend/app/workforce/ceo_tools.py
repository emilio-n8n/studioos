"""CEO tool implementations — each is an async function that returns a dict."""

import json
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.project import Project
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role
from app.models.agent import Agent
from app.models.task import Task
from app.kernel.event_store import event_store

logger = logging.getLogger("studioos.ceo_tools")


async def get_project_status(project_id: int, db: Session) -> dict:
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        return {"error": "Project not found"}
    return {
        "name": proj.name,
        "description": proj.description,
        "status": proj.status,
        "complexity": proj.complexity,
        "created_at": str(proj.created_at) if proj.created_at else None,
    }


async def get_org_tree(project_id: int, db: Session) -> dict:
    org = db.query(Organization).options(
        joinedload(Organization.departments)
        .joinedload(Department.roles)
        .joinedload(Role.agents)
    ).filter(Organization.project_id == project_id).first()
    if not org:
        return {"error": "Organization not found"}

    departments = []
    for dept in org.departments:
        roles_list = []
        for role in dept.roles:
            agents_list = [
                {
                    "id": a.id,
                    "name": a.name,
                    "status": a.status,
                    "is_active": a.is_active,
                    "agent_type": a.agent_type,
                    "provider": a.provider,
                }
                for a in role.agents
            ]
            roles_list.append({
                "id": role.id,
                "title": role.title,
                "level": role.level or 1,
                "is_governance": role.is_governance or False,
                "agents": agents_list,
            })
        departments.append({
            "id": dept.id,
            "name": dept.name,
            "description": dept.description,
            "roles": roles_list,
        })
    return {
        "org_name": org.name,
        "structure_type": org.structure_type,
        "departments": departments,
    }


async def list_agents(project_id: int, db: Session) -> dict:
    agents = (
        db.query(Agent)
        .join(Role, Agent.role_id == Role.id)
        .join(Department, Role.department_id == Department.id)
        .join(Organization, Department.organization_id == Organization.id)
        .filter(Organization.project_id == project_id)
        .options(joinedload(Agent.current_task))
        .all()
    )
    result = []
    for a in agents:
        task_title = a.current_task.title if a.current_task else None
        result.append({
            "id": a.id,
            "name": a.name,
            "status": a.status,
            "is_active": a.is_active,
            "agent_type": a.agent_type,
            "provider": a.provider,
            "current_task": task_title,
            "last_active_at": str(a.last_active_at) if a.last_active_at else None,
        })
    return {"agents": result}


async def get_agent_detail(project_id: int, agent_id: int, db: Session) -> dict:
    agent = (
        db.query(Agent)
        .options(joinedload(Agent.current_task), joinedload(Agent.role))
        .filter(Agent.id == agent_id)
        .first()
    )
    if not agent:
        return {"error": "Agent not found"}
    task_title = agent.current_task.title if agent.current_task else None
    role_title = agent.role.title if agent.role else None

    recent_files = []
    try:
        from app.kernel import git_manager
        all_commits = git_manager.get_log(project_id, max_count=50)
        for c in all_commits:
            if agent.name.lower() in c.get("author", "").lower():
                recent_files.append({
                    "sha": c.get("hexsha", "")[:8],
                    "message": c.get("message", ""),
                    "timestamp": c.get("datetime", ""),
                })
                if len(recent_files) >= 5:
                    break
    except Exception as e:
        logger.warning(f"Could not fetch commits for agent {agent_id}: {e}")

    return {
        "id": agent.id,
        "name": agent.name,
        "role": role_title,
        "status": agent.status,
        "is_active": agent.is_active,
        "agent_type": agent.agent_type,
        "provider": agent.provider,
        "capabilities": agent.capabilities or [],
        "current_task": task_title,
        "last_active_at": str(agent.last_active_at) if agent.last_active_at else None,
        "recent_files": recent_files,
    }


async def run_pipeline(project_id: int, db: Session) -> dict:
    from app.api.pipeline import _execute_pipeline
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        return {"error": "Project not found"}
    try:
        result = await _execute_pipeline(proj, db)
        return {"status": "completed", "result": result}
    except Exception as e:
        logger.exception(f"Pipeline failed for project {project_id}")
        return {"status": "failed", "error": str(e)}


async def send_message_to_agent(project_id: int, agent_id: int, message: str, db: Session) -> dict:
    from app.kernel.event_bus import event_bus, EVENT_AGENT_MESSAGE
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return {"error": "Agent not found"}
    await event_bus.emit_to_project(project_id, EVENT_AGENT_MESSAGE, {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "message": message,
        "sender": "CEO",
        "timestamp": str(datetime.now(timezone.utc)),
    }, db)
    return {"status": "sent", "agent_name": agent.name}


async def get_recent_events(project_id: int, db: Session, limit: int = 20) -> dict:
    events = event_store.replay(db, project_id, limit=limit)
    return {
        "events": [
            {
                "type": e.event_type,
                "data": e.data,
                "timestamp": str(e.created_at) if e.created_at else None,
            }
            for e in events
        ]
    }


async def get_dashboard(project_id: int, db: Session) -> dict:
    proj = db.query(Project).options(
        joinedload(Project.organization)
        .joinedload(Organization.departments)
        .joinedload(Department.roles)
        .joinedload(Role.agents)
    ).filter(Project.id == project_id).first()
    if not proj:
        return {"error": "Project not found"}

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    tasks_by_status = {}
    for t in tasks:
        tasks_by_status[t.status] = tasks_by_status.get(t.status, 0) + 1

    org = proj.organization
    dept_count = len(org.departments) if org else 0
    role_count = sum(len(d.roles) for d in org.departments) if org else 0
    agent_count = sum(len(r.agents) for d in org.departments for r in d.roles) if org else 0

    return {
        "project_id": project_id,
        "total_tasks": len(tasks),
        "tasks_by_status": tasks_by_status,
        "total_agents": agent_count,
        "total_roles": role_count,
        "total_departments": dept_count,
        "complexity": proj.complexity,
    }
