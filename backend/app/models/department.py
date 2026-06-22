from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, remote, foreign

from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    parent_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    organization = relationship("Organization", back_populates="departments")
    roles = relationship("Role", back_populates="department", cascade="all, delete-orphan")

    parent = relationship(
        "Department", remote_side=[id], back_populates="children",
        foreign_keys=[parent_department_id],
    )
    children = relationship(
        "Department", back_populates="parent",
        foreign_keys=[parent_department_id],
    )
