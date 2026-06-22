from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.agent_registry import AgentRegistryEntry
from app.integration.base import (
    AgentProviderInterface,
    AgentManifest,
    Capability,
)

logger = logging.getLogger("studioos.integration.registry")


class AgentRegistry:
    def auto_discover(
        self,
        db: Session,
        providers: list[AgentProviderInterface],
    ) -> int:
        discovered = 0
        for provider in providers:
            try:
                import asyncio
                manifests = asyncio.run(provider.discover_agents())
            except Exception as e:
                logger.warning(
                    f"Discovery failed for {type(provider).__name__}: {e}"
                )
                continue

            for manifest in manifests:
                existing = (
                    db.query(AgentRegistryEntry)
                    .filter(
                        AgentRegistryEntry.provider == manifest.provider,
                        AgentRegistryEntry.external_id
                        == manifest.external_id,
                    )
                    .first()
                )
                if existing:
                    existing.name = manifest.name
                    existing.description = manifest.description
                    existing.capabilities = [
                        c.name for c in manifest.capabilities
                    ]
                    existing.cost = manifest.cost
                    existing.speed = manifest.speed
                    existing.quality = manifest.quality
                    existing.extra_data = manifest.metadata
                else:
                    entry = AgentRegistryEntry(
                        provider=manifest.provider,
                        external_id=manifest.external_id,
                        name=manifest.name,
                        description=manifest.description,
                        capabilities=[
                            c.name for c in manifest.capabilities
                        ],
                        cost=manifest.cost,
                        speed=manifest.speed,
                        quality=manifest.quality,
                        status="discovered",
                        endpoint_url=None,
                        extra_data=manifest.metadata,
                    )
                    db.add(entry)
                    discovered += 1

        db.commit()
        logger.info(
            f"Auto-discovery: {discovered} new agents registered"
        )
        return discovered

    def register_manual(
        self,
        db: Session,
        provider: str,
        name: str,
        description: str,
        capabilities: list[str],
        endpoint_url: str | None = None,
        cost: int = 5,
        speed: int = 5,
        quality: int = 5,
    ) -> AgentRegistryEntry:
        existing = (
            db.query(AgentRegistryEntry)
            .filter(
                AgentRegistryEntry.provider == provider,
                AgentRegistryEntry.name == name,
            )
            .first()
        )
        if existing:
            raise ValueError(
                f"Agent '{name}' from provider '{provider}' "
                f"already exists (id={existing.id})"
            )

        entry = AgentRegistryEntry(
            provider=provider,
            external_id=name.lower().replace(" ", "_"),
            name=name,
            description=description,
            capabilities=capabilities,
            cost=cost,
            speed=speed,
            quality=quality,
            status="pending",
                endpoint_url=endpoint_url,
                extra_data={},
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        logger.info(
            f"Manual registration: '{name}' ({provider}) → entry #{entry.id}"
        )
        return entry

    def approve(
        self, db: Session, entry_id: int
    ) -> AgentRegistryEntry | None:
        entry = (
            db.query(AgentRegistryEntry)
            .filter(AgentRegistryEntry.id == entry_id)
            .first()
        )
        if not entry:
            return None
        entry.status = "approved"
        db.commit()
        db.refresh(entry)
        logger.info(f"Agent registry entry #{entry_id} approved")
        return entry

    def reject(
        self, db: Session, entry_id: int
    ) -> AgentRegistryEntry | None:
        entry = (
            db.query(AgentRegistryEntry)
            .filter(AgentRegistryEntry.id == entry_id)
            .first()
        )
        if not entry:
            return None
        entry.status = "rejected"
        db.commit()
        db.refresh(entry)
        logger.info(f"Agent registry entry #{entry_id} rejected")
        return entry

    def search_by_capability(
        self,
        db: Session,
        capabilities: list[str],
        min_quality: int = 1,
    ) -> list[AgentRegistryEntry]:
        all_entries = (
            db.query(AgentRegistryEntry)
            .filter(
                AgentRegistryEntry.status == "approved",
                AgentRegistryEntry.quality >= min_quality,
            )
            .all()
        )
        results = []
        for entry in all_entries:
            entry_caps = set(entry.capabilities or [])
            if entry_caps.intersection(capabilities):
                results.append(entry)
        return sorted(
            results,
            key=lambda e: (
                -len(
                    set(e.capabilities or []).intersection(capabilities)
                ),
                -e.quality,
                -e.speed,
                e.cost,
            ),
        )

    def list_all(
        self,
        db: Session,
        status: str | None = None,
        provider: str | None = None,
    ) -> list[AgentRegistryEntry]:
        q = db.query(AgentRegistryEntry)
        if status:
            q = q.filter(AgentRegistryEntry.status == status)
        if provider:
            q = q.filter(AgentRegistryEntry.provider == provider)
        return q.order_by(
            AgentRegistryEntry.created_at.desc()
        ).all()

    def get_by_id(
        self, db: Session, entry_id: int
    ) -> AgentRegistryEntry | None:
        return (
            db.query(AgentRegistryEntry)
            .filter(AgentRegistryEntry.id == entry_id)
            .first()
        )


registry = AgentRegistry()
