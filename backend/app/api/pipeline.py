import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.config import settings
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
from app.integration.native_provider import NativeProvider
from app.integration.mock_provider import MockProvider
from app.integration.registry import registry
from app.integration.dispatcher import TaskDispatcher
from app.integration.base import TaskResult
from app.workforce.agent_executor import generate_website_files
from app.workforce.file_manager import file_manager
from app.api.generation import _demo_html, _demo_css, _demo_js
from app.workforce.task_executor import generate_task_output
from app.kernel import git_manager
from app.models.pull_request_model import PullRequest

logger = logging.getLogger("studioos.pipeline")
router = APIRouter(prefix="/api/projects/{project_id}/pipeline", tags=["pipeline"])


STATUS_COLORS = {
    "TODO": "#94a3b8",
    "ASSIGNED": "#60a5fa",
    "IN_PROGRESS": "#fbbf24",
    "REVIEW": "#f97316",
    "APPROVED": "#22c55e",
    "MERGED": "#14b8a6",
    "COMPLETED": "#22c55e",
    "ARCHIVED": "#64748b",
    "FAILED": "#ef4444",
}


@router.get("/dag")
def get_pipeline_dag(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    nodes = []
    edges = []
    for t in tasks:
        color = STATUS_COLORS.get(t.status, "#94a3b8")
        agent_name = t.assigned_agent.name if t.assigned_agent else None
        nodes.append({
            "id": f"task-{t.id}",
            "type": "taskNode",
            "position": {"x": 0, "y": 0},
            "data": {
                "label": t.title,
                "status": t.status,
                "priority": t.priority,
                "agent": agent_name,
                "color": color,
            },
        })
        for dep in (t.depends_on or []):
            edges.append({
                "id": f"dep-{dep}-{t.id}",
                "source": f"task-{dep}",
                "target": f"task-{t.id}",
                "type": "smoothstep",
                "animated": True,
            })
    return {"nodes": nodes, "edges": edges}


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
            "description": t.description or "",
            "depends_on": t.depends_on or [],
            "status": t.status,
        }
        for t in tasks
    ]

    scheduler = Scheduler(task_dicts)
    completed_ids: set[int] = set()
    failed_ids: set[int] = set()
    total = len(tasks)

    await event_bus.emit_to_project(project_id, EVENT_PIPELINE_STAGE_COMPLETED, {
        "stage": "dag_initialized", "tasks": total,
    }, db)

    is_demo = project.openai_api_key and project.openai_api_key.strip().lower() == "demo"

    while not scheduler.is_done():
        ready = scheduler.get_ready()
        if not ready:
            break

        # Emit TASK_STARTED for all ready tasks
        for task_data in ready:
            tid = task_data["id"]
            task = db.query(Task).filter(Task.id == tid).first()
            if not task:
                continue
            task.status = "IN_PROGRESS"
            await event_bus.emit_to_project(project_id, EVENT_TASK_STARTED, {
                "task_id": tid, "title": task.title,
            }, db)
        db.commit()

        # Execute each ready task
        for task_data in ready:
            tid = task_data["id"]
            task = db.query(Task).filter(Task.id == tid).first()
            if not task:
                continue
            try:
                if is_demo:
                    await _execute_demo_task(task, project, db)
                else:
                    await _execute_llm_task(task, project, db)
                task.status = "COMPLETED"
                completed_ids.add(tid)
                scheduler.mark_completed(tid)
                await event_bus.emit_to_project(project_id, EVENT_TASK_COMPLETED, {
                    "task_id": tid, "title": task.title, "status": "COMPLETED",
                }, db)
            except Exception as e:
                task.status = "FAILED"
                failed_ids.add(tid)
                logger.error(f"Task #{tid} failed: {e}")
            db.commit()

    # Generate overall project output
    if completed_ids:
        await _generate_output(project, db, is_demo)

    project.status = "completed" if not failed_ids else "completed_with_errors"
    db.commit()

    return {
        "tasks_completed": len(completed_ids),
        "tasks_failed": len(failed_ids),
        "tasks_total": total,
    }


async def _execute_demo_task(task: Task, project: Project, db: Session):
    agent = db.query(Agent).filter(Agent.id == task.assigned_agent_id).first()
    role = db.query(Role).filter(Role.id == agent.role_id).first() if agent else None
    dept = db.query(Department).filter(Department.id == role.department_id).first() if role else None

    files = [{
        "path": f"output/{task.id}/report.md",
        "content": (
            f"# {task.title}\n\n"
            f"Completed by {agent.name if agent else 'unknown'} "
            f"({role.title if role else 'unknown'}) "
            f"in {dept.name if dept else 'unknown'}.\n\n"
            f"Demo execution \u2014 no real LLM call."
        ),
    }]

    await _save_and_commit(task, project, agent, files, db)


async def _execute_llm_task(task: Task, project: Project, db: Session):
    agent = db.query(Agent).filter(Agent.id == task.assigned_agent_id).first()
    role = db.query(Role).filter(Role.id == agent.role_id).first() if agent else None
    dept = db.query(Department).filter(Department.id == role.department_id).first() if role else None

    project_summary = (project.analysis or {}).get("summary", "")

    files = await generate_task_output(
        task_title=task.title,
        task_description=task.description or "",
        role_title=role.title if role else "Worker",
        department_name=dept.name if dept else "General",
        project_name=project.name,
        project_summary=project_summary,
        task_id=task.id,
        api_key=project.openai_api_key or "",
        provider=project.provider or "openai",
        model=project.model or None,
    )

    await _save_and_commit(task, project, agent, files, db)


async def _save_and_commit(
    task: Task,
    project: Project,
    agent: Agent | None,
    files: list[dict],
    db: Session,
):
    import asyncio

    agent_name = agent.name if agent else "worker"
    output_path = project.output_path if project.output_path else None

    await asyncio.to_thread(
        file_manager.save_website, project.id, files, output_path
    )

    try:
        sha = git_manager.commit_work(
            project.id, agent_name,
            {f["path"]: f["content"] for f in files},
            f"Task #{task.id}: {task.title}",
        )
        logger.info(f"Task #{task.id} committed by {agent_name}: {sha[:8]}")

        branch = f"agent/{agent_name.replace(' ', '_').lower()}"
        pr = PullRequest(
            project_id=project.id,
            agent_id=agent.id if agent else None,
            source_branch=branch,
            target_branch="main",
            status="open",
            title=f"Task #{task.id}: {task.title}",
            description=f"Auto-generated PR for task #{task.id} by {agent_name}",
        )
        db.add(pr)
        db.commit()
        db.refresh(pr)
        logger.info(f"Auto PR #{pr.id} created for task #{task.id}")

        try:
            git_manager.merge_branch(project.id, branch, "main")
            pr.status = "merged"
            db.commit()
            logger.info(f"Auto PR #{pr.id} merged for task #{task.id}")
        except Exception as merge_err:
            logger.warning(f"Auto-merge failed for PR #{pr.id}: {merge_err}")

    except Exception as e:
        logger.warning(f"Git commit failed for task #{task.id}: {e}")


def _build_dispatcher() -> TaskDispatcher:
    providers: list[Any] = [
        NativeProvider(),
        MockProvider(delay=1.0),
    ]
    urls = [u.strip() for u in settings.acp_server_urls.split(",") if u.strip()]
    if urls:
        from app.integration.acp_provider import ACPProvider
        providers.append(ACPProvider(urls))
        logger.info(f"ACP provider configured: {urls}")
    return TaskDispatcher(registry, providers)


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
    output_dir = await asyncio.to_thread(file_manager.save_website, project_id, files, project.output_path)
    output_url = await asyncio.to_thread(file_manager.get_output_url, project_id, project.output_path)
    logger.info(f"Pipeline output generated at {output_dir}")
