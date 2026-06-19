import asyncio
import json
import logging
from typing import Callable, Any

from fastapi import WebSocket

logger = logging.getLogger("studioos.event_bus")


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

    async def emit_to_project(self, project_id: int, event_type: str, data: Any = None):
        payload = json.dumps({"type": event_type, "data": data}, default=str)
        dead = []
        for ws in list(self._websockets.get(project_id, [])):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"WebSocket send error for project {project_id}: {e}")
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
