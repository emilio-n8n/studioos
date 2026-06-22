from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.integration.base import (
    AgentProviderInterface,
    TaskSpec,
    RunStatus,
    TaskResult,
)
from app.integration.registry import AgentRegistry

logger = logging.getLogger("studioos.integration.dispatcher")

MAX_RETRIES = 3
POLL_INTERVAL = 1.0
TASK_TIMEOUT = 120.0


class TaskDispatcher:
    def __init__(
        self,
        registry: AgentRegistry,
        providers: list[AgentProviderInterface],
    ):
        self._registry = registry
        self._providers = providers

    async def dispatch_task(
        self,
        task: dict[str, Any],
        project_context: dict[str, Any],
        db: Session,
    ) -> TaskResult:
        required_caps = self._infer_capabilities(task)

        # Find best agent from registry
        entries = self._registry.search_by_capability(
            db, required_caps, min_quality=1
        )

        if entries:
            entry = entries[0]
            provider = self._find_provider(entry.provider)
            agent_id = entry.external_id
            logger.info(
                f"[Dispatcher] Task #{task['id']} → "
                f"'{entry.name}' ({entry.provider}, score={entries[0].quality})"
            )
        else:
            provider = self._find_provider("native")
            agent_id = "executor"
            logger.info(
                f"[Dispatcher] Task #{task['id']} → "
                f"no capability match, using native executor"
            )

        if not provider:
            return TaskResult(
                run_id="",
                status="failed",
                output={},
                error="No provider available for task",
            )

        spec = TaskSpec(
            task_id=task["id"],
            title=task.get("title", "Untitled"),
            description=task.get("description", ""),
            context=project_context,
            required_capabilities=required_caps,
            max_timeout=TASK_TIMEOUT,
        )

        run_id = await provider.assign_task(agent_id, spec)
        result = await self._poll_with_retry(provider, run_id)

        # Write result to memory
        if result.status == "completed":
            self._store_result(db, task["id"], result)

        return result

    async def dispatch_batch(
        self,
        tasks: list[dict[str, Any]],
        project_context: dict[str, Any],
        db: Session,
    ) -> list[TaskResult]:
        if not tasks:
            return []

        logger.info(
            f"[Dispatcher] Dispatching batch of {len(tasks)} tasks "
            f"in parallel"
        )

        results = await asyncio.gather(
            *[
                self.dispatch_task(task, project_context, db)
                for task in tasks
            ],
            return_exceptions=True,
        )

        final: list[TaskResult] = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.error(
                    f"[Dispatcher] Task batch failed for task "
                    f"#{tasks[i]['id']}: {r}"
                )
                final.append(
                    TaskResult(
                        run_id="",
                        status="failed",
                        output={},
                        error=str(r),
                    )
                )
            else:
                final.append(r)

        return final

    async def _poll_with_retry(
        self,
        provider: AgentProviderInterface,
        run_id: str,
    ) -> TaskResult:
        for attempt in range(MAX_RETRIES):
            try:
                status = await asyncio.wait_for(
                    self._poll(provider, run_id),
                    timeout=TASK_TIMEOUT,
                )
                if status.status == "completed":
                    return await provider.collect_results(run_id)
                if status.status == "failed" and attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"[Dispatcher] Run {run_id[:8]} failed, "
                        f"retrying ({attempt + 1}/{MAX_RETRIES})"
                    )
                    continue
                return await provider.collect_results(run_id)
            except asyncio.TimeoutError:
                logger.warning(
                    f"[Dispatcher] Run {run_id[:8]} timed out "
                    f"({attempt + 1}/{MAX_RETRIES})"
                )
                if attempt < MAX_RETRIES - 1:
                    continue
                return TaskResult(
                    run_id=run_id,
                    status="failed",
                    output={},
                    error=f"Timed out after {TASK_TIMEOUT}s",
                )

        return TaskResult(
            run_id=run_id,
            status="failed",
            output={},
            error="Max retries exceeded",
        )

    async def _poll(
        self,
        provider: AgentProviderInterface,
        run_id: str,
    ) -> RunStatus:
        while True:
            status = await provider.get_status(run_id)
            if status.status in ("completed", "failed"):
                return status
            await asyncio.sleep(POLL_INTERVAL)

    def _find_provider(
        self, provider_name: str
    ) -> AgentProviderInterface | None:
        for p in self._providers:
            class_name = type(p).__name__.lower()
            if provider_name in class_name:
                return p
            if provider_name == "native" and "native" in class_name:
                return p
            if provider_name == "mock" and "mock" in class_name:
                return p
            if provider_name == "acp" and "acp" in class_name:
                return p
        return None

    def _infer_capabilities(
        self, task: dict[str, Any]
    ) -> list[str]:
        title = (task.get("title") or "").lower()
        desc = (task.get("description") or "").lower()
        text = f"{title} {desc}"

        caps = []
        keywords = {
            "backend": ["backend", "api", "server", "database", "python"],
            "frontend": ["frontend", "ui", "css", "html", "react"],
            "writing": ["write", "content", "documentation", "narrative"],
            "design": ["design", "ui", "ux", "visual"],
            "testing": ["test", "qa", "quality"],
        }
        for cap, words in keywords.items():
            if any(w in text for w in words):
                caps.append(cap)

        return caps if caps else ["general"]

    def _store_result(
        self,
        db: Session,
        task_id: int,
        result: TaskResult,
    ):
        from app.kernel.memory_system import memory_system

        memory_system.store(
            db,
            project_id=0,
            key=f"task_{task_id}_result",
            value={
                "run_id": result.run_id,
                "status": result.status,
                "output_summary": str(result.output.get("message", ""))[
                    :500
                ],
            },
            type="task_result",
        )
        try:
            db.commit()
        except Exception:
            db.rollback()


dispatcher = TaskDispatcher.__new__(TaskDispatcher)
