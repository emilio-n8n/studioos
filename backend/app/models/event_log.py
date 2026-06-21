from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, JSON, DateTime

from app.database import Base


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, default=dict)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    sequence = Column(Integer, nullable=False, default=0)
