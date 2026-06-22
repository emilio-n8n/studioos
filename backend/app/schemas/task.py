from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class TaskResponse(BaseModel):
    id: int
    project_id: int
    department_id: int | None
    assigned_agent_id: int | None
    title: str
    description: str | None
    priority: int
    status: str
    estimated_cost: float
    depends_on: list
    created_at: datetime

    class Config:
        from_attributes = True


VALID_STATUSES = Literal["TODO", "ASSIGNED", "IN_PROGRESS", "REVIEW", "APPROVED", "MERGED", "ARCHIVED"]

class TaskTransition(BaseModel):
    status: VALID_STATUSES


class DashboardResponse(BaseModel):
    project_id: int
    total_tasks: int
    tasks_by_status: dict[str, int]
    total_agents: int
    total_roles: int
    total_departments: int
    complexity: str | None
    risks: list | None
    total_decisions: int = 0
    governance_agents: int = 0
    execution_agents: int = 0
    native_agents: int = 0
    acp_agents: int = 0
    mock_agents: int = 0
    level_4: int = 0  # CEO
    level_3: int = 0  # Director
    level_2: int = 0  # Lead
    level_1: int = 0  # Worker
    total_events: int = 0
