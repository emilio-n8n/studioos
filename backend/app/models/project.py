from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="analyzing")
    complexity = Column(String(50), nullable=True)
    provider = Column(String(50), default="openai")
    model = Column(String(100), nullable=True)
    openai_api_key = Column(String(255), nullable=True)
    analysis = Column(JSON, nullable=True)
    output_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="project", uselist=False, cascade="all, delete-orphan")
