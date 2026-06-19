from sqlalchemy import Column, Integer, String, ForeignKey, JSON

from app.database import Base
from sqlalchemy.orm import relationship


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="created")

    role = relationship("Role", back_populates="agents")
