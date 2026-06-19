import logging
import asyncio
from contextvars import ContextVar

current_project_id: ContextVar[int | None] = ContextVar("current_project_id", default=None)


class WebSocketLogHandler(logging.Handler):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus

    def emit(self, record: logging.LogRecord):
        pid = current_project_id.get()
        if pid is None:
            return
        try:
            msg = self.format(record)
            data = {
                "level": record.levelname,
                "message": msg,
                "logger": record.name,
                "timestamp": record.created,
            }
            asyncio.ensure_future(self.event_bus.emit_to_project(pid, "log", data))
        except Exception:
            self.handleError(record)


def set_project_context(project_id: int | None):
    current_project_id.set(project_id)
