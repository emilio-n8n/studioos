import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.config import settings
from app.integration.registry import registry
from app.integration.native_provider import NativeProvider
from app.integration.mock_provider import MockProvider

logger = logging.getLogger("studioos.integration.api")
router = APIRouter(prefix="/api/integration", tags=["integration"])

_PROVIDERS: list[Any] = [
    NativeProvider(),
    MockProvider(delay=1.0),
]


def _init_providers():
    urls = [u.strip() for u in settings.acp_server_urls.split(",") if u.strip()]
    if urls:
        from app.integration.acp_provider import ACPProvider
        _PROVIDERS.append(ACPProvider(urls))
        logger.info(f"ACP provider configured: {urls}")


_init_providers()


class RegisterAgentBody(BaseModel):
    provider: str
    name: str
    description: str = ""
    capabilities: list[str] = []
    endpoint_url: str | None = None
    cost: int = 5
    speed: int = 5
    quality: int = 5


@router.get("/providers")
def list_providers():
    return {
        "providers": [
            {
                "name": type(p).__name__.replace("Provider", "").lower(),
                "class": type(p).__name__,
            }
            for p in _PROVIDERS
        ]
    }


@router.post("/providers/discover")
def discover_agents(db: Session = Depends(get_db)):
    count = registry.auto_discover(db, _PROVIDERS)
    return {"discovered": count, "total": len(registry.list_all(db))}


@router.get("/agents")
def list_registry_agents(
    status: str | None = Query(None),
    provider: str | None = Query(None),
    db: Session = Depends(get_db),
):
    entries = registry.list_all(db, status=status, provider=provider)
    return [
        {
            "id": e.id,
            "provider": e.provider,
            "external_id": e.external_id,
            "name": e.name,
            "description": e.description,
            "capabilities": e.capabilities or [],
            "cost": e.cost,
            "speed": e.speed,
            "quality": e.quality,
            "status": e.status,
            "endpoint_url": e.endpoint_url,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]


@router.post("/agents/register", status_code=201)
def register_agent(body: RegisterAgentBody, db: Session = Depends(get_db)):
    try:
        entry = registry.register_manual(
            db=db,
            provider=body.provider,
            name=body.name,
            description=body.description,
            capabilities=body.capabilities,
            endpoint_url=body.endpoint_url,
            cost=body.cost,
            speed=body.speed,
            quality=body.quality,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {
        "id": entry.id,
        "provider": entry.provider,
        "name": entry.name,
        "status": entry.status,
    }


@router.post("/agents/{entry_id}/approve")
def approve_agent(entry_id: int, db: Session = Depends(get_db)):
    entry = registry.approve(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": entry.id,
        "name": entry.name,
        "status": entry.status,
    }


@router.post("/agents/{entry_id}/reject")
def reject_agent(entry_id: int, db: Session = Depends(get_db)):
    entry = registry.reject(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": entry.id,
        "name": entry.name,
        "status": entry.status,
    }


@router.get("/agents/search")
def search_agents(
    q: str = Query(..., description="Comma-separated capabilities"),
    min_quality: int = Query(1),
    db: Session = Depends(get_db),
):
    capabilities = [c.strip() for c in q.split(",") if c.strip()]
    if not capabilities:
        raise HTTPException(
            status_code=400, detail="At least one capability required"
        )
    results = registry.search_by_capability(
        db, capabilities, min_quality=min_quality
    )
    return [
        {
            "id": e.id,
            "provider": e.provider,
            "name": e.name,
            "capabilities": e.capabilities or [],
            "cost": e.cost,
            "speed": e.speed,
            "quality": e.quality,
            "score": len(
                set(e.capabilities or []).intersection(capabilities)
            ),
        }
        for e in results
    ]


@router.get("/agents/{entry_id}")
def get_agent(entry_id: int, db: Session = Depends(get_db)):
    entry = registry.get_by_id(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": entry.id,
        "provider": entry.provider,
        "external_id": entry.external_id,
        "name": entry.name,
        "description": entry.description,
        "capabilities": entry.capabilities or [],
        "cost": entry.cost,
        "speed": entry.speed,
        "quality": entry.quality,
        "status": entry.status,
        "endpoint_url": entry.endpoint_url,
        "created_at": entry.created_at.isoformat(),
    }
