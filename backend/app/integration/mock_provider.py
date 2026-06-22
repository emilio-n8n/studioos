from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.integration.base import (
    AgentProviderInterface,
    AgentManifest,
    Capability,
    TaskSpec,
    RunStatus,
    TaskResult,
)

logger = logging.getLogger("studioos.integration.mock_provider")

_MOCK_AGENTS: list[AgentManifest] = [
    AgentManifest(
        external_id="backend_dev",
        name="Backend Developer (Mock)",
        description="Builds APIs, models, and database logic",
        provider="mock",
        capabilities=[
            Capability("backend", 8),
            Capability("python", 9),
            Capability("api", 8),
            Capability("database", 7),
        ],
        cost=6,
        speed=7,
        quality=8,
    ),
    AgentManifest(
        external_id="frontend_dev",
        name="Frontend Developer (Mock)",
        description="Creates UI components and responsive layouts",
        provider="mock",
        capabilities=[
            Capability("frontend", 8),
            Capability("typescript", 7),
            Capability("css", 8),
            Capability("ui", 7),
        ],
        cost=5,
        speed=8,
        quality=7,
    ),
    AgentManifest(
        external_id="writer",
        name="Content Writer (Mock)",
        description="Writes documentation, copy, and narrative content",
        provider="mock",
        capabilities=[
            Capability("writing", 9),
            Capability("documentation", 8),
            Capability("content", 8),
        ],
        cost=3,
        speed=9,
        quality=8,
    ),
]


class MockProvider(AgentProviderInterface):
    def __init__(self, delay: float = 2.0):
        self._delay = delay
        self._runs: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def discover_agents(self) -> list[AgentManifest]:
        return _MOCK_AGENTS.copy()

    async def get_capabilities(
        self, agent_id: str
    ) -> list[Capability]:
        for a in _MOCK_AGENTS:
            if a.external_id == agent_id:
                return a.capabilities.copy()
        return []

    async def assign_task(
        self, agent_id: str, task: TaskSpec
    ) -> str:
        self._counter += 1
        run_id = f"mock-{self._counter}"
        self._runs[run_id] = {
            "run_id": run_id,
            "agent_id": agent_id,
            "task": task,
            "status": "running",
            "progress": 0.0,
            "started_at": asyncio.get_event_loop().time(),
        }
        logger.info(
            f"[MockProvider] Assigned task #{task.task_id} "
            f"to mock agent '{agent_id}' → run {run_id}"
        )
        return run_id

    async def get_status(self, run_id: str) -> RunStatus:
        run = self._runs.get(run_id)
        if not run:
            return RunStatus(run_id=run_id, status="failed")

        elapsed = asyncio.get_event_loop().time() - run["started_at"]
        run["progress"] = min(elapsed / self._delay, 1.0)

        if run["progress"] >= 1.0 and run["status"] == "running":
            run["status"] = "completed"
            run["result"] = self._mock_result(run)

        return RunStatus(
            run_id=run_id,
            status=run["status"],
            progress=run["progress"],
        )

    async def collect_results(self, run_id: str) -> TaskResult:
        run = self._runs.get(run_id)
        if not run:
            return TaskResult(
                run_id=run_id, status="failed", output={},
                error="Run not found"
            )
        result = run.get("result", {})
        return TaskResult(
            run_id=run_id,
            status=run["status"],
            output=result,
            duration_seconds=min(self._delay, self._delay),
        )

    async def cancel_task(self, run_id: str) -> bool:
        run = self._runs.get(run_id)
        if run and run["status"] == "running":
            run["status"] = "cancelled"
            return True
        return False

    def _mock_result(
        self, run: dict[str, Any]
    ) -> dict[str, Any]:
        task = run["task"]
        agent_id = run["agent_id"]
        return {
            "message": f"[Mock] {agent_id} completed task #{task.task_id}",
            "files": {
                f"output/{task.task_id}/report.md": (
                    f"# Task Report: {task.title}\n\n"
                    f"Completed by {agent_id}.\n\n"
                    f"## Description\n{task.description}\n\n"
                    f"## Results\nMock execution completed successfully."
                )
            },
        }
