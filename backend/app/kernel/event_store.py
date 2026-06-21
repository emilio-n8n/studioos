from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.event_log import EventLog


class EventStore:
    def append(
        self,
        db: Session,
        project_id: int,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> EventLog:
        last = (
            db.query(EventLog)
            .filter(EventLog.project_id == project_id)
            .order_by(EventLog.sequence.desc())
            .first()
        )
        next_seq = (last.sequence + 1) if last else 1

        entry = EventLog(
            project_id=project_id,
            event_type=event_type,
            payload=payload or {},
            timestamp=datetime.now(timezone.utc),
            sequence=next_seq,
        )
        db.add(entry)
        db.flush()
        return entry

    def replay(
        self,
        db: Session,
        project_id: int,
        since_id: int | None = None,
        limit: int = 1000,
    ) -> list[EventLog]:
        q = db.query(EventLog).filter(EventLog.project_id == project_id)
        if since_id:
            q = q.filter(EventLog.id > since_id)
        return q.order_by(EventLog.sequence.asc()).limit(limit).all()

    def replay_by_type(
        self,
        db: Session,
        project_id: int,
        event_type: str,
        limit: int = 1000,
    ) -> list[EventLog]:
        return (
            db.query(EventLog)
            .filter(
                EventLog.project_id == project_id,
                EventLog.event_type == event_type,
            )
            .order_by(EventLog.sequence.asc())
            .limit(limit)
            .all()
        )

    def count(self, db: Session, project_id: int) -> int:
        return (
            db.query(EventLog)
            .filter(EventLog.project_id == project_id)
            .count()
        )


event_store = EventStore()
