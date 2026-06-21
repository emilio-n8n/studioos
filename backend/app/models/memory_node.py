from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MemoryNode(Base):
    __tablename__ = "memory_nodes"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("memory_nodes.id"), nullable=True)

    key = Column(String(255), nullable=False, index=True)
    value = Column(JSON, nullable=False, default=dict)
    type = Column(String(50), default="fact")
    tags = Column(JSON, default=list)
    status = Column(String(50), default="active")
    version = Column(Integer, default=1)
    summary = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    approved_by = Column(String(255), nullable=True)
    superseded_by = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    children = relationship("MemoryNode", backref="parent", remote_side=[id])
