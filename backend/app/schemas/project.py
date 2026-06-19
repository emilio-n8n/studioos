from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    openai_api_key: str = Field(min_length=1, max_length=200)
    provider: str = Field(default="openai", pattern=r"^(openai|opencode-go)$")
    model: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str
    complexity: str | None
    provider: str
    model: str | None
    analysis: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectListItem(BaseModel):
    id: int
    name: str
    description: str
    status: str
    complexity: str | None
    created_at: datetime

    class Config:
        from_attributes = True
