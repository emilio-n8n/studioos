from __future__ import annotations
from pydantic import BaseModel


class RoleResponse(BaseModel):
    id: int
    title: str
    summary: str | None
    responsibilities: list
    authority: list
    permissions: list
    reports_to: str | None
    required_skills: list
    metrics: list
    status: str
    is_governance: bool = False
    level: int = 1

    class Config:
        from_attributes = True


class AgentResponse(BaseModel):
    id: int
    role_id: int
    name: str
    status: str
    agent_type: str = "execution"
    provider: str = "native"
    capabilities: list = []

    class Config:
        from_attributes = True


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    parent_department_id: int | None = None
    roles: list[RoleResponse] = []

    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    id: int
    project_id: int
    name: str
    structure_type: str
    hierarchy: list
    departments: list[DepartmentResponse] = []

    class Config:
        from_attributes = True
