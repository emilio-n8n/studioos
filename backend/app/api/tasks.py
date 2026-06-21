import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.task import Task
from app.models.project import Project
from app.models.organization import Organization, StrategicDecision
from app.models.department import Department
from app.models.role import Role
from app.schemas.task import TaskResponse, TaskTransition, DashboardResponse
from app.kernel.task_engine import is_valid_transition, can_transition_to
from app.kernel.event_bus import event_bus, EVENT_TASK_ASSIGNED, EVENT_TASK_STARTED, EVENT_TASK_COMPLETED
from app.kernel.memory_system import memory_system
from app.kernel.log_handler import set_project_context

logger = logging.getLogger("studioos.tasks")
router = APIRouter(prefix="/api/projects/{project_id}/tasks", tags=["tasks"])

_EVENT_MAP = {
    "ASSIGNED": EVENT_TASK_ASSIGNED,
    "IN_PROGRESS": EVENT_TASK_STARTED,
    "APPROVED": EVENT_TASK_COMPLETED,
    "MERGED": EVENT_TASK_COMPLETED,
    "ARCHIVED": EVENT_TASK_COMPLETED,
}


@router.get("")
def list_tasks(project_id: int, db: Session = Depends(get_db)):
    tasks = db.query(Task).filter(Task.project_id == project_id).order_by(Task.priority.desc(), Task.created_at).all()
    return tasks


@router.get("/dashboard")
def get_dashboard(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).options(
        joinedload(Project.organization)
        .joinedload(Organization.departments)
        .joinedload(Department.roles)
        .joinedload(Role.agents)
    ).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    tasks_by_status = {}
    for t in tasks:
        tasks_by_status[t.status] = tasks_by_status.get(t.status, 0) + 1

    org = project.organization
    dept_count = len(org.departments) if org else 0
    role_count = sum(len(d.roles) for d in org.departments) if org else 0
    agent_count = sum(len(r.agents) for d in org.departments for r in d.roles) if org else 0

    decision_count = db.query(StrategicDecision).filter(
        StrategicDecision.project_id == project_id
    ).count()

    return DashboardResponse(
        project_id=project.id,
        total_tasks=len(tasks),
        tasks_by_status=tasks_by_status,
        total_agents=agent_count,
        total_roles=role_count,
        total_departments=dept_count,
        complexity=project.complexity,
        risks=(project.analysis or {}).get("risks", []),
        total_decisions=decision_count,
    )


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def transition_task(project_id: int, task_id: int, body: TaskTransition, db: Session = Depends(get_db)):
    set_project_context(project_id)
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    allowed, reason = can_transition_to(db, task.id, task.status, body.status)
    if not allowed:
        raise HTTPException(status_code=400, detail=reason)

    old_status = task.status
    task.status = body.status
    logger.info(f"Task #{task_id} '{task.title}': {old_status} → {body.status}")
    memory_system.log_audit(db, project_id, "task_transition", "Workflow",
                            {"task_id": task.id, "title": task.title, "from": old_status, "to": body.status})
    db.commit()
    db.refresh(task)

    event_type = _EVENT_MAP.get(body.status)
    if event_type:
        await event_bus.emit_to_project(project_id, event_type, {
            "task_id": task.id,
            "title": task.title,
            "status": task.status,
            "old_status": old_status,
        }, db)

    return task
