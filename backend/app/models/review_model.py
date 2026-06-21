from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Text

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    worker_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    status = Column(String(50), default="pending")
    output_ref = Column(JSON, default=dict)
    comments = Column(JSON, default=list)
    attempt = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
