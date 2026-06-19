from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    hierarchy = Column(JSON, default=list)

    project = relationship("Project", back_populates="organization")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
