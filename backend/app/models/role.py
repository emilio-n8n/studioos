from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    title = Column(String(255), nullable=False)
    responsibilities = Column(JSON, default=list)
    authority = Column(JSON, default=list)
    reports_to = Column(String(255), nullable=True)
    required_skills = Column(JSON, default=list)

    department = relationship("Department", back_populates="roles")
    agents = relationship("Agent", back_populates="role", cascade="all, delete-orphan")
