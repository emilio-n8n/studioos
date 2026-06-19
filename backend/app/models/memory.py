from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime

from app.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(JSON, nullable=True)
    type = Column(String(50), default="general")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    action = Column(String(255), nullable=False)
    actor = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
