import logging
from datetime import datetime, timezone
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.agent import Agent
from app.models.pull_request_model import PullRequest
from app.kernel import git_manager
from app.kernel.event_bus import event_bus

logger = logging.getLogger("studioos.git")
router = APIRouter(prefix="/api/projects/{project_id}/git", tags=["git"])


class CommitBody(BaseModel):
    agent_id: int
    files: dict[str, str]
    message: str = "Work commit"


class PRBody(BaseModel):
    agent_id: int
    title: str = "Work submission"
    description: str = ""


@router.post("/init")
def init_project_git(project_id: int):
    path = git_manager.init_repo(project_id)
    return {"repo_path": path, "status": "initialized"}


@router.get("/log")
def get_git_log(project_id: int):
    try:
        commits = git_manager.get_log(project_id)
        return {"commits": commits}
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/branches")
def get_git_branches(project_id: int):
    try:
        branches = git_manager.get_branches(project_id)
        return {"branches": branches}
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/commit")
async def commit_agent_work(
    project_id: int,
    body: CommitBody = Body(...),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == body.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        sha = git_manager.commit_work(project_id, agent.name, body.files, body.message)
        await event_bus.emit_to_project(project_id, "git_commit", {
            "agent_id": body.agent_id, "hexsha": sha, "message": body.message,
        })
        return {"hexsha": sha, "message": body.message}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pr")
async def create_pull_request(
    project_id: int,
    body: PRBody = Body(...),
    db: Session = Depends(get_db),
):
    agent = db.query(Agent).filter(Agent.id == body.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    branch = f"agent/{agent.name.replace(' ', '_').lower()}"

    pr = PullRequest(
        project_id=project_id,
        agent_id=agent.id,
        source_branch=branch,
        target_branch="main",
        status="open",
        title=body.title,
        description=body.description,
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)

    await event_bus.emit_to_project(project_id, "pr_created", {
        "pr_id": pr.id, "agent_id": body.agent_id, "branch": branch,
    })
    return {"pr_id": pr.id, "status": "open", "branch": branch}


@router.get("/prs")
def list_pull_requests(project_id: int, db: Session = Depends(get_db)):
    prs = db.query(PullRequest).filter(
        PullRequest.project_id == project_id
    ).order_by(PullRequest.created_at.desc()).all()
    return [
        {
            "id": pr.id,
            "agent_id": pr.agent_id,
            "source_branch": pr.source_branch,
            "target_branch": pr.target_branch,
            "status": pr.status,
            "title": pr.title,
            "description": pr.description,
            "created_at": pr.created_at.isoformat(),
            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
        }
        for pr in prs
    ]


@router.post("/pr/{pr_id}/merge")
async def merge_pull_request(project_id: int, pr_id: int, db: Session = Depends(get_db)):
    pr = db.query(PullRequest).filter(
        PullRequest.id == pr_id, PullRequest.project_id == project_id
    ).first()
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    if pr.status != "open":
        raise HTTPException(status_code=400, detail=f"PR is {pr.status}, not open")

    try:
        git_manager.merge_branch(project_id, pr.source_branch, pr.target_branch)
        pr.status = "merged"
        pr.merged_at = datetime.now(timezone.utc)
        db.commit()

        await event_bus.emit_to_project(project_id, "pr_merged", {
            "pr_id": pr.id, "branch": pr.source_branch,
        })
        return {"pr_id": pr.id, "status": "merged"}
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
