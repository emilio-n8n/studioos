from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, JSON, DateTime, Text

from app.database import Base


class AgentRegistryEntry(Base):
    __tablename__ = "agent_registry"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    capabilities = Column(JSON, default=list)
    cost = Column(Integer, default=5)
    speed = Column(Integer, default=5)
    quality = Column(Integer, default=5)
    status = Column(String(50), default="discovered", index=True)
    endpoint_url = Column(String(500), nullable=True)
    extra_data = Column("metadata", JSON, default=dict)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
