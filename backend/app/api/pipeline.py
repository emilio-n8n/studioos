import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.project import Project
from app.models.organization import Organization
from app.models.department import Department
from app.models.role import Role
from app.models.agent import Agent
from app.models.task import Task
from app.kernel.event_bus import (
    event_bus,
    EVENT_PIPELINE_STARTED,
    EVENT_PIPELINE_STAGE_COMPLETED,
    EVENT_PIPELINE_COMPLETED,
    EVENT_PIPELINE_FAILED,
    EVENT_TASK_STARTED,
    EVENT_TASK_COMPLETED,
)
from app.kernel.scheduler import Scheduler
from app.kernel.memory_system import memory_system
from app.kernel.log_handler import set_project_context
from app.workforce.agent_executor import generate_website_files
from app.workforce.file_manager import file_manager
from app.api.generation import _demo_html, _demo_css, _demo_js

logger = logging.getLogger("studioos.pipeline")
router = APIRouter(prefix="/api/projects/{project_id}/pipeline", tags=["pipeline"])


@router.post("/run")
async def run_pipeline(project_id: int, db: Session = Depends(get_db)):
    set_project_context(project_id)

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await event_bus.emit_to_project(project_id, EVENT_PIPELINE_STARTED, {
        "project_id": project_id, "status": "running",
    }, db)

    try:
        result = await _execute_pipeline(project, db)
        await event_bus.emit_to_project(project_id, EVENT_PIPELINE_COMPLETED, {
            "project_id": project_id, "status": "completed", **result,
        }, db)
        return {"status": "completed", **result}
    except Exception as e:
        logger.exception(f"Pipeline failed for project {project_id}")
        await event_bus.emit_to_project(project_id, EVENT_PIPELINE_FAILED, {
            "project_id": project_id, "error": str(e),
        }, db)
        raise HTTPException(status_code=500, detail=str(e))


async def _execute_pipeline(project: Project, db: Session) -> dict:
    project_id = project.id
    tasks = db.query(Task).filter(Task.project_id == project_id).all()

    if not tasks:
        return {"message": "No tasks to execute", "tasks_completed": 0}

    task_dicts = [
        {
            "id": t.id,
            "title": t.title,
            "depends_on": t.depends_on or [],
            "status": t.status,
        }
        for t in tasks
    ]

    scheduler = Scheduler(task_dicts)
    completed_ids: set[int] = set()
    total = len(tasks)

    await event_bus.emit_to_project(project_id, EVENT_PIPELINE_STAGE_COMPLETED, {
        "stage": "dag_initialized", "tasks": total,
    }, db)

    is_demo = project.openai_api_key and project.openai_api_key.strip().lower() == "demo"

    while not scheduler.is_done():
        ready = scheduler.get_ready()
        for task_data in ready:
            tid = task_data["id"]
            task = db.query(Task).filter(Task.id == tid).first()
            if not task:
                continue

            await event_bus.emit_to_project(project_id, EVENT_TASK_STARTED, {
                "task_id": tid, "title": task.title,
            }, db)

            task.status = "IN_PROGRESS"
            db.commit()

            try:
                if is_demo:
                    _execute_demo_task(task)
                else:
                    await _execute_llm_task(task, project, db)

                task.status = "COMPLETED"
                db.commit()
                completed_ids.add(tid)
                scheduler.mark_completed(tid)

                await event_bus.emit_to_project(project_id, EVENT_TASK_COMPLETED, {
                    "task_id": tid, "title": task.title, "status": "COMPLETED",
                }, db)
            except Exception as e:
                logger.error(f"Task #{tid} failed: {e}")
                task.status = "FAILED"
                db.commit()

        if not ready:
            break

    # Generate output
    await _generate_output(project, db, is_demo)

    project.status = "completed"
    db.commit()

    return {
        "tasks_completed": len(completed_ids),
        "tasks_total": total,
    }


def _execute_demo_task(task: Task):
    import time
    time.sleep(0.1)


async def _execute_llm_task(task: Task, project: Project, db: Session):
    pass


async def _generate_output(project: Project, db: Session, is_demo: bool):
    project_id = project.id
    if is_demo:
        files = [
            {"path": "index.html", "content": _demo_html(project)},
            {"path": "css/style.css", "content": _demo_css()},
            {"path": "js/main.js", "content": _demo_js()},
        ]
    else:
        org = db.query(Organization).options(
            joinedload(Organization.departments).joinedload(Department.roles).joinedload(Role.agents)
        ).filter(Organization.project_id == project_id).first()
        if not org:
            return

        departments_data = [
            {"name": d.name, "description": d.description}
            for d in org.departments
        ]
        roles_data = []
        for d in org.departments:
            for r in d.roles:
                roles_data.append({
                    "title": r.title,
                    "department_name": d.name,
                    "responsibilities": r.responsibilities,
                })

        analysis = project.analysis or {}
        files = await generate_website_files(
            project_name=project.name,
            project_description=project.description,
            analysis=analysis,
            departments=departments_data,
            roles=roles_data,
            api_key=project.openai_api_key or "",
            provider=project.provider or "openai",
            model=project.model or None,
        )

    import asyncio
    output_dir = await asyncio.to_thread(file_manager.save_website, project_id, files)
    output_url = await asyncio.to_thread(file_manager.get_output_url, project_id)
    logger.info(f"Pipeline output generated at {output_dir}")
