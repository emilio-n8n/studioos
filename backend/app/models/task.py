from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Float, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=0)
    status = Column(String(50), default="TODO")
    estimated_cost = Column(Float, default=0.0)
    depends_on = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", backref="tasks")
    department = relationship("Department")
    assigned_agent = relationship("Agent")
