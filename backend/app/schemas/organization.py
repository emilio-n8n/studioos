from pydantic import BaseModel


class RoleResponse(BaseModel):
    id: int
    title: str
    responsibilities: list
    authority: list
    reports_to: str | None
    required_skills: list

    class Config:
        from_attributes = True


class AgentResponse(BaseModel):
    id: int
    role_id: int
    name: str
    status: str

    class Config:
        from_attributes = True


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    roles: list[RoleResponse] = []

    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    id: int
    project_id: int
    name: str
    hierarchy: list
    departments: list[DepartmentResponse] = []

    class Config:
        from_attributes = True
