from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class MemoryNodeCreate(BaseModel):
    key: str
    value: dict
    type: str = "fact"
    tags: list[str] = []
    parent_id: int | None = None
    summary: str | None = None
    created_by: str | None = None


class MemoryNodeResponse(BaseModel):
    id: int
    project_id: int
    agent_id: int | None
    parent_id: int | None
    key: str
    value: dict
    type: str
    tags: list
    status: str
    version: int
    summary: str | None
    created_by: str | None
    approved_by: str | None
    superseded_by: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MemoryNodeUpdate(BaseModel):
    status: str | None = None
    approved_by: str | None = None
    superseded_by: int | None = None


class MemoryGraphResponse(BaseModel):
    nodes: list[MemoryNodeResponse]
    edges: list[dict]
