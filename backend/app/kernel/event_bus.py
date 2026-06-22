import asyncio
import json
import logging
from typing import Any, Callable

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.kernel.event_store import event_store

logger = logging.getLogger("studioos.event_bus")

# Event types
EVENT_PROJECT_CREATED = "PROJECT_CREATED"
EVENT_STRATEGY_GENERATED = "STRATEGY_GENERATED"
EVENT_ORG_CREATED = "ORG_CREATED"
EVENT_AGENT_SPAWNED = "AGENT_SPAWNED"
EVENT_TASK_ASSIGNED = "TASK_ASSIGNED"
EVENT_TASK_STARTED = "TASK_STARTED"
EVENT_TASK_COMPLETED = "TASK_COMPLETED"
EVENT_REVIEW_REQUESTED = "REVIEW_REQUESTED"
EVENT_REVIEW_APPROVED = "REVIEW_APPROVED"
EVENT_REVIEW_CHANGES_REQUESTED = "REVIEW_CHANGES_REQUESTED"
EVENT_GIT_COMMIT_CREATED = "GIT_COMMIT_CREATED"
EVENT_PR_CREATED = "PR_CREATED"
EVENT_PR_MERGED = "PR_MERGED"
EVENT_MEMORY_CREATED = "MEMORY_CREATED"
EVENT_PIPELINE_STARTED = "PIPELINE_STARTED"
EVENT_PIPELINE_STAGE_COMPLETED = "PIPELINE_STAGE_COMPLETED"
EVENT_PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
EVENT_PIPELINE_FAILED = "PIPELINE_FAILED"
EVENT_AGENT_STATUS_CHANGE = "AGENT_STATUS_CHANGE"
EVENT_AGENT_MESSAGE = "AGENT_MESSAGE"


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._websockets: dict[int, list[WebSocket]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    async def emit(self, event_type: str, data: Any = None):
        for callback in list(self._subscribers.get(event_type, [])):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.exception(f"EventBus error in {event_type}: {e}")

    async def emit_to_project(
        self,
        project_id: int,
        event_type: str,
        data: Any = None,
        db: Session | None = None,
    ):
        if db is not None:
            try:
                event_store.append(db, project_id, event_type, data)
                db.commit()
            except Exception as e:
                logger.warning(f"EventStore append error: {e}")

        payload = json.dumps(
            {"type": event_type, "data": data}, default=str
        )
        dead = []
        for ws in list(self._websockets.get(project_id, [])):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(
                    f"WebSocket send error for project {project_id}: {e}"
                )
                dead.append(ws)
        for ws in dead:
            self.unregister_ws(project_id, ws)

    def register_ws(self, project_id: int, ws: WebSocket):
        if project_id not in self._websockets:
            self._websockets[project_id] = []
        self._websockets[project_id].append(ws)

    def unregister_ws(self, project_id: int, ws: WebSocket):
        if project_id in self._websockets:
            try:
                self._websockets[project_id].remove(ws)
            except ValueError:
                pass


event_bus = EventBus()
