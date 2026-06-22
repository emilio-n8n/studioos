from sqlalchemy import Column, Integer, String, ForeignKey, JSON

from app.database import Base
from sqlalchemy.orm import relationship


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="created")
    agent_type = Column(String(50), default="execution")
    provider = Column(String(50), default="native")
    external_agent_id = Column(String(255), nullable=True)
    capabilities = Column(JSON, default=list)

    role = relationship("Role", back_populates="agents")
