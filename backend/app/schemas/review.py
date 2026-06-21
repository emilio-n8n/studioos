from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class ReviewResponse(BaseModel):
    id: int
    task_id: int
    project_id: int
    reviewer_id: int | None
    worker_id: int | None
    status: str
    output_ref: dict
    comments: list
    attempt: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewApprove(BaseModel):
    approved_by: str | None = None
    comment: str | None = None


class ReviewRequestChanges(BaseModel):
    comment: str
