from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    responsibilities = Column(JSON, default=list)
    authority = Column(JSON, default=list)
    permissions = Column(JSON, default=list)
    reports_to = Column(String(255), nullable=True)
    required_skills = Column(JSON, default=list)
    metrics = Column(JSON, default=list)
    status = Column(String(50), default="active")
    is_governance = Column(Boolean, default=False)
    level = Column(Integer, default=1)

    department = relationship("Department", back_populates="roles")
    agents = relationship("Agent", back_populates="role", cascade="all, delete-orphan")
