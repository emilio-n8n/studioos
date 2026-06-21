import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.agent import Agent
from app.models.review_model import Review
from app.models.role import Role
from app.schemas.review import ReviewResponse, ReviewApprove, ReviewRequestChanges
from app.kernel.task_engine import is_valid_transition, can_transition_to
from app.kernel.event_bus import event_bus, EVENT_REVIEW_REQUESTED, EVENT_REVIEW_APPROVED, EVENT_REVIEW_CHANGES_REQUESTED

logger = logging.getLogger("studioos.reviews")
router = APIRouter(prefix="/api/projects/{project_id}/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewResponse])
def list_reviews(project_id: int, status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Review).filter(Review.project_id == project_id)
    if status:
        q = q.filter(Review.status == status)
    return q.order_by(Review.created_at.desc()).all()


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(project_id: int, review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id, Review.project_id == project_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@router.post("/{review_id}/approve", response_model=ReviewResponse)
async def approve_review(project_id: int, review_id: int, body: ReviewApprove, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id, Review.project_id == project_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != "pending":
        raise HTTPException(status_code=400, detail=f"Review is {review.status}, not pending")

    review.status = "approved"
    if body.comment:
        review.comments = review.comments + [{"type": "approve", "text": body.comment, "by": body.approved_by or "reviewer"}]

    task = db.query(Task).filter(Task.id == review.task_id).first()
    if task and is_valid_transition(task.status, "APPROVED"):
        task.status = "APPROVED"
        logger.info(f"Task #{task.id} approved via review #{review.id}")

    db.commit()
    db.refresh(review)
    await event_bus.emit_to_project(project_id, EVENT_REVIEW_APPROVED, {"review_id": review.id, "task_id": review.task_id}, db)
    return review


@router.post("/{review_id}/request-changes", response_model=ReviewResponse)
async def request_changes(project_id: int, review_id: int, body: ReviewRequestChanges, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id, Review.project_id == project_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != "pending":
        raise HTTPException(status_code=400, detail=f"Review is {review.status}, not pending")

    review.status = "changes_requested"
    review.comments = review.comments + [{"type": "request_changes", "text": body.comment}]
    review.attempt += 1

    task = db.query(Task).filter(Task.id == review.task_id).first()
    if task and is_valid_transition(task.status, "IN_PROGRESS"):
        task.status = "IN_PROGRESS"

    db.commit()
    db.refresh(review)
    await event_bus.emit_to_project(project_id, EVENT_REVIEW_CHANGES_REQUESTED, {"review_id": review.id, "task_id": review.task_id}, db)
    return review


@router.post("/submit", response_model=ReviewResponse)
async def submit_for_review(
    project_id: int,
    task_id: int,
    worker_id: int,
    output_ref: dict = {},
    db: Session = Depends(get_db),
):
    task = db.query(Task).filter(Task.id == task_id, Task.project_id == project_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not is_valid_transition(task.status, "REVIEW"):
        raise HTTPException(status_code=400, detail=f"Cannot submit task in status {task.status}")

    worker = db.query(Agent).filter(Agent.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    role = db.query(Role).filter(Role.id == worker.role_id).first()
    department_id = role.department_id if role else None

    # Find a Lead-level reviewer from same department
    reviewer = (
        db.query(Agent)
        .join(Role)
        .filter(
            Role.department_id == department_id,
            Agent.id != worker.id,
            Agent.status == "active",
        )
        .order_by(Role.id.desc())
        .first()
    )
    reviewer_id = reviewer.id if reviewer else None

    review = Review(
        task_id=task.id,
        project_id=project_id,
        reviewer_id=reviewer_id,
        worker_id=worker.id,
        status="pending",
        output_ref=output_ref,
        comments=[],
        attempt=1,
    )
    db.add(review)
    task.status = "REVIEW"
    db.commit()
    db.refresh(review)
    logger.info(f"Review #{review.id} created for task #{task_id} by agent #{worker_id}")

    await event_bus.emit_to_project(project_id, EVENT_REVIEW_REQUESTED, {
        "review_id": review.id, "task_id": task_id, "worker_id": worker_id,
    }, db)
    return review
