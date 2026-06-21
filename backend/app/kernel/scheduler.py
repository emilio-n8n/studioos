from __future__ import annotations

from typing import Any

from app.kernel.dag_engine import DAG

TASK_PENDING = "TODO"
TASK_READY = "READY"
TASK_RUNNING = "RUNNING"
TASK_COMPLETED = "COMPLETED"
TASK_FAILED = "FAILED"
TASK_BLOCKED = "BLOCKED"


class Scheduler:
    def __init__(self, tasks: list[dict[str, Any]]):
        self._dag = DAG(tasks)
        self._tasks = {t["id"]: t for t in tasks}
        self._completed: set[int] = set()

    def get_ready(self) -> list[dict[str, Any]]:
        return self._dag.get_ready_tasks(self._completed)

    def mark_completed(self, task_id: int) -> list[dict[str, Any]]:
        if task_id in self._tasks:
            self._completed.add(task_id)
        return self.get_ready()

    def mark_failed(self, task_id: int):
        pass

    def is_done(self) -> bool:
        return len(self._completed) >= len(self._tasks)

    def get_status(self) -> dict[int, str]:
        statuses = {}
        for tid in self._tasks:
            if tid in self._completed:
                statuses[tid] = TASK_COMPLETED
            elif tid in {t["id"] for t in self.get_ready()}:
                statuses[tid] = TASK_READY
            else:
                statuses[tid] = TASK_BLOCKED
        return statuses

    def get_progress(self) -> dict[str, Any]:
        return {
            "total": len(self._tasks),
            "completed": len(self._completed),
            "remaining": len(self._tasks) - len(self._completed),
            "statuses": self.get_status(),
        }
