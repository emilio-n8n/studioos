from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime

from app.database import Base


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    reviewer_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    source_branch = Column(String(255), nullable=False)
    target_branch = Column(String(255), default="main")
    status = Column(String(50), default="open")
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    merged_at = Column(DateTime, nullable=True)
