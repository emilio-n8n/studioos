from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Capability:
    name: str
    level: int = 1


@dataclass
class AgentManifest:
    external_id: str
    name: str
    description: str
    provider: str
    capabilities: list[Capability]
    cost: int = 5
    speed: int = 5
    quality: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskSpec:
    task_id: int
    title: str
    description: str
    context: dict[str, Any]
    required_capabilities: list[str]
    max_timeout: int = 120


@dataclass
class RunStatus:
    run_id: str
    status: str
    progress: float = 0.0


@dataclass
class TaskResult:
    run_id: str
    status: str
    output: dict[str, Any]
    error: str | None = None
    cost_incurred: float = 0.0
    duration_seconds: float = 0.0


class AgentProviderInterface(ABC):
    @abstractmethod
    async def discover_agents(self) -> list[AgentManifest]:
        ...

    @abstractmethod
    async def get_capabilities(
        self, agent_id: str
    ) -> list[Capability]:
        ...

    @abstractmethod
    async def assign_task(
        self, agent_id: str, task: TaskSpec
    ) -> str:
        ...

    @abstractmethod
    async def get_status(self, run_id: str) -> RunStatus:
        ...

    @abstractmethod
    async def collect_results(self, run_id: str) -> TaskResult:
        ...

    @abstractmethod
    async def cancel_task(self, run_id: str) -> bool:
        ...
