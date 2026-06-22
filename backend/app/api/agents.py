import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.agent import Agent
from app.models.role import Role
from app.models.department import Department
from app.models.organization import Organization
from app.kernel.event_bus import event_bus, EVENT_AGENT_MESSAGE

logger = logging.getLogger("studioos.agents")
router = APIRouter(prefix="/api/projects/{project_id}/agents", tags=["agents"])


class AgentMessageBody(BaseModel):
    message: str
    sender: str


def _get_agents_for_project(project_id: int, db: Session):
    return (
        db.query(Agent)
        .join(Agent.role)
        .join(Role.department)
        .join(Department.organization)
        .options(
            joinedload(Agent.role),
            joinedload(Agent.current_task),
        )
        .filter(Organization.project_id == project_id)
        .all()
    )


def _agent_to_dict(agent: Agent):
    return {
        "id": agent.id,
        "name": agent.name,
        "role_title": agent.role.title if agent.role else None,
        "department_name": agent.role.department.name if agent.role and agent.role.department else None,
        "status": agent.status,
        "agent_type": agent.agent_type,
        "provider": agent.provider,
        "is_active": agent.is_active,
        "capabilities": agent.capabilities or [],
        "current_task_id": agent.current_task_id,
        "current_task_title": agent.current_task.title if agent.current_task else None,
        "last_active_at": str(agent.last_active_at) if agent.last_active_at else None,
    }


@router.get("")
def list_agents(project_id: int, db: Session = Depends(get_db)):
    agents = _get_agents_for_project(project_id, db)
    return {"agents": [_agent_to_dict(a) for a in agents]}


@router.get("/{agent_id}")
def get_agent(project_id: int, agent_id: int, db: Session = Depends(get_db)):
    agents = _get_agents_for_project(project_id, db)
    agent = next((a for a in agents if a.id == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    data = _agent_to_dict(agent)
    data["recent_files"] = []
    return data


@router.post("/{agent_id}/message")
async def send_message(
    project_id: int,
    agent_id: int,
    body: AgentMessageBody,
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    await event_bus.emit_to_project(project_id, EVENT_AGENT_MESSAGE, {
        "agent_id": agent_id,
        "agent_name": agent.name,
        "message": body.message,
        "sender": body.sender,
    }, db)

    return {"status": "sent"}
