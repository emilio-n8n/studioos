from __future__ import annotations

from typing import Any


class CycleError(Exception):
    pass


class DAG:
    def __init__(self, tasks: list[dict[str, Any]]):
        self._tasks = {t["id"]: t for t in tasks}
        self._edges: dict[int, list[int]] = {}
        for t in tasks:
            deps = t.get("depends_on") or []
            self._edges[t["id"]] = [d for d in deps if d in self._tasks]

    def validate(self) -> list[int]:
        order = []
        visited: dict[int, str] = {}

        def dfs(node_id: int):
            if node_id in visited:
                if visited[node_id] == "visiting":
                    raise CycleError(f"Cycle detected involving task {node_id}")
                return
            visited[node_id] = "visiting"
            for dep in self._edges.get(node_id, []):
                if dep in self._tasks:
                    dfs(dep)
            visited[node_id] = "done"
            order.append(node_id)

        for tid in self._tasks:
            if tid not in visited:
                dfs(tid)

        return order

    def get_ready_tasks(
        self, completed_ids: set[int]
    ) -> list[dict[str, Any]]:
        ready = []
        for tid, task in self._tasks.items():
            if tid in completed_ids:
                continue
            deps = task.get("depends_on") or []
            if all(d in completed_ids for d in deps):
                ready.append(task)
        return ready

    def get_execution_batches(
        self, completed_ids: set[int] | None = None
    ) -> list[list[dict[str, Any]]]:
        completed = set(completed_ids or [])
        order = self.validate()
        remaining = [tid for tid in order if tid not in completed]
        batches = []

        while remaining:
            batch = []
            still_remaining = []
            for tid in remaining:
                deps = self._edges.get(tid, [])
                if all(d in completed for d in deps if d in self._tasks):
                    batch.append(self._tasks[tid])
                else:
                    still_remaining.append(tid)
            if not batch:
                raise CycleError(
                    f"Stuck — no ready tasks, {len(still_remaining)} remain"
                )
            batches.append(batch)
            completed.update(t["id"] for t in batch)
            remaining = still_remaining

        return batches
