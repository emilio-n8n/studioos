from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.review_model import Review

VALID_TRANSITIONS = {
    "TODO": ["ASSIGNED", "IN_PROGRESS"],
    "ASSIGNED": ["IN_PROGRESS", "TODO"],
    "IN_PROGRESS": ["REVIEW", "ASSIGNED"],
    "REVIEW": ["APPROVED", "IN_PROGRESS"],
    "APPROVED": ["MERGED", "REVIEW"],
    "MERGED": ["ARCHIVED", "APPROVED"],
    "ARCHIVED": [],
}

FINAL_STATUSES = {"APPROVED", "MERGED", "ARCHIVED"}


def is_valid_transition(current: str, target: str) -> bool:
    return target in VALID_TRANSITIONS.get(current, [])


def has_approved_review(db: Session, task_id: int) -> bool:
    review = (
        db.query(Review)
        .filter(Review.task_id == task_id, Review.status == "approved")
        .first()
    )
    return review is not None


def can_transition_to(
    db: Session, task_id: int, current: str, target: str
) -> tuple[bool, str]:
    if not is_valid_transition(current, target):
        return False, f"Transition {current} → {target} is not allowed"

    if target in FINAL_STATUSES and target != "APPROVED":
        if not has_approved_review(db, task_id):
            return (
                False,
                f"Cannot transition to {target} without an approved review",
            )

    return True, ""
