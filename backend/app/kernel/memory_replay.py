from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.event_log import EventLog


class MemoryReplay:
    def get_snapshot(
        self, db: Session, project_id: int
    ) -> dict[str, Any]:
        events = (
            db.query(EventLog)
            .filter(EventLog.project_id == project_id)
            .order_by(EventLog.sequence.asc())
            .all()
        )
        return self._build_state(events)

    def get_snapshot_at(
        self, db: Session, project_id: int, timestamp: datetime
    ) -> dict[str, Any]:
        events = (
            db.query(EventLog)
            .filter(
                EventLog.project_id == project_id,
                EventLog.timestamp <= timestamp,
            )
            .order_by(EventLog.sequence.asc())
            .all()
        )
        return self._build_state(events)

    def replay(
        self, db: Session, project_id: int
    ) -> list[dict[str, Any]]:
        events = (
            db.query(EventLog)
            .filter(EventLog.project_id == project_id)
            .order_by(EventLog.sequence.asc())
            .all()
        )
        return [
            {
                "id": e.id,
                "sequence": e.sequence,
                "event_type": e.event_type,
                "payload": e.payload,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in events
        ]

    def _build_state(
        self, events: list[EventLog]
    ) -> dict[str, Any]:
        state: dict[str, Any] = {
            "project": None,
            "strategy": None,
            "organization": None,
            "agents": [],
            "tasks": {},
            "reviews": [],
            "memories": [],
            "events_count": len(events),
        }
        for e in events:
            p = e.payload or {}
            if e.event_type == "PROJECT_CREATED":
                state["project"] = p
            elif e.event_type == "STRATEGY_GENERATED":
                state["strategy"] = p
            elif e.event_type == "ORG_CREATED":
                state["organization"] = p
            elif e.event_type == "AGENT_SPAWNED":
                state["agents"].append(p)
            elif e.event_type in ("TASK_STARTED", "TASK_COMPLETED"):
                tid = str(p.get("task_id"))
                state["tasks"][tid] = {
                    "id": p.get("task_id"),
                    "title": p.get("title"),
                    "event": e.event_type,
                    "status": p.get("status", e.event_type),
                }
            elif e.event_type == "MEMORY_CREATED":
                state["memories"].append(p)
            elif "REVIEW" in e.event_type:
                state["reviews"].append(p)
        return state


memory_replay = MemoryReplay()
