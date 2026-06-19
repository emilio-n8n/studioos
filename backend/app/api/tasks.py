import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.task import Task
from app.models.project import Project
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role
from app.schemas.task import TaskResponse, TaskTransition, DashboardResponse
from app.kernel.task_engine import is_valid_transition
from app.kernel.event_bus import event_bus
from app.kernel.memory_system import memory_system

logger = logging.getLogger("studioos.tasks")
router = APIRouter(prefix="/api/projects/{project_id}/tasks", tags=["tasks"])


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

    return DashboardResponse(
        project_id=project.id,
        total_tasks=len(tasks),
        tasks_by_status=tasks_by_status,
        total_agents=agent_count,
        total_roles=role_count,
        total_departments=dept_count,
        complexity=project.complexity,
        risks=(project.analysis or {}).get("risks", []),
    )


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def transition_task(project_id: int, task_id: int, body: TaskTransition, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if not is_valid_transition(task.status, body.status):
        raise HTTPException(status_code=400, detail=f"Invalid transition from {task.status} to {body.status}")

    old_status = task.status
    task.status = body.status
    memory_system.log_audit(db, project_id, "task_transition", "Workflow",
                            {"task_id": task.id, "title": task.title, "from": old_status, "to": body.status})
    db.commit()
    db.refresh(task)

    try:
        await event_bus.emit_to_project(project_id, "task_updated", {
            "task_id": task.id,
            "title": task.title,
            "status": task.status,
        })
    except Exception as e:
        logger.warning(f"Event bus emit failed: {e}")

    return task
