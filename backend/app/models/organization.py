from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    structure_type = Column(String(50), default="hierarchical")
    hierarchy = Column(JSON, default=list)

    project = relationship("Project", back_populates="organization")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")


class StrategicDecision(Base):
    __tablename__ = "strategic_decisions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    impact = Column(String(50), nullable=True)
    extra = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
