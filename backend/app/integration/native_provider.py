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

logger = logging.getLogger("studioos.integration.native_provider")

_NATIVE_AGENTS: list[AgentManifest] = [
    AgentManifest(
        external_id="planner",
        name="Strategic Planner",
        description="Analyzes project descriptions and produces strategic analysis",
        provider="native",
        capabilities=[
            Capability("strategic_planning", 9),
            Capability("analysis", 8),
            Capability("project_design", 7),
        ],
        cost=2,
        speed=7,
        quality=8,
    ),
    AgentManifest(
        external_id="architect",
        name="Organization Architect",
        description="Designs organizational structures from strategic analysis",
        provider="native",
        capabilities=[
            Capability("org_design", 9),
            Capability("hierarchy_planning", 8),
        ],
        cost=2,
        speed=8,
        quality=8,
    ),
    AgentManifest(
        external_id="recruiter",
        name="Recruiter",
        description="Defines roles, required skills, and matches agents to positions",
        provider="native",
        capabilities=[
            Capability("recruiting", 8),
            Capability("role_design", 7),
            Capability("skill_matching", 7),
        ],
        cost=1,
        speed=9,
        quality=7,
    ),
    AgentManifest(
        external_id="executor",
        name="Agent Executor",
        description="Executes tasks and generates output files",
        provider="native",
        capabilities=[
            Capability("code_generation", 7),
            Capability("content_creation", 7),
        ],
        cost=3,
        speed=6,
        quality=7,
    ),
]


class NativeProvider(AgentProviderInterface):
    def __init__(self):
        self._runs: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    async def discover_agents(self) -> list[AgentManifest]:
        return _NATIVE_AGENTS.copy()

    async def get_capabilities(
        self, agent_id: str
    ) -> list[Capability]:
        for a in _NATIVE_AGENTS:
            if a.external_id == agent_id:
                return a.capabilities.copy()
        return []

    async def assign_task(
        self, agent_id: str, task: TaskSpec
    ) -> str:
        self._counter += 1
        run_id = f"native-{self._counter}"
        self._runs[run_id] = {
            "run_id": run_id,
            "agent_id": agent_id,
            "task": task,
            "status": "running",
            "progress": 0.0,
        }
        logger.info(
            f"[NativeProvider] Assigned task #{task.task_id} "
            f"to agent '{agent_id}' → run {run_id}"
        )
        return run_id

    async def get_status(self, run_id: str) -> RunStatus:
        run = self._runs.get(run_id)
        if not run:
            return RunStatus(run_id=run_id, status="failed")
        run["progress"] = min(run["progress"] + 0.5, 1.0)
        if run["progress"] >= 1.0:
            run["status"] = "completed"
            run["result"] = {
                "message": f"Task completed by native agent {run['agent_id']}",
                "files": {},
            }
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
            duration_seconds=0.1,
        )

    async def cancel_task(self, run_id: str) -> bool:
        run = self._runs.get(run_id)
        if run:
            run["status"] = "cancelled"
            return True
        return False
