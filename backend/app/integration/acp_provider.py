from __future__ import annotations

import logging
from typing import Any

import httpx

from app.integration.base import (
    AgentProviderInterface,
    AgentManifest,
    Capability,
    TaskSpec,
    RunStatus,
    TaskResult,
)

logger = logging.getLogger("studioos.integration.acp_provider")


class ACPProvider(AgentProviderInterface):
    def __init__(self, server_urls: list[str]):
        self._server_urls = server_urls
        self._client = httpx.AsyncClient(timeout=30.0)

    async def discover_agents(self) -> list[AgentManifest]:
        manifests: list[AgentManifest] = []
        for url in self._server_urls:
            try:
                resp = await self._client.get(f"{url}/agents")
                resp.raise_for_status()
                data = resp.json()
                for agent_data in data.get("agents", []):
                    meta = agent_data.get("metadata", {})
                    caps_raw = meta.get("capabilities", [])
                    manifests.append(
                        AgentManifest(
                            external_id=agent_data["name"],
                            name=agent_data.get(
                                "name", agent_data["name"]
                            ),
                            description=agent_data.get(
                                "description", ""
                            ),
                            provider="acp",
                            capabilities=[
                                Capability(name=c) for c in caps_raw
                            ],
                            cost=meta.get("cost", 5),
                            speed=meta.get("speed", 5),
                            quality=meta.get("quality", 5),
                            metadata={
                                "server_url": url,
                                **agent_data.get("metadata", {}),
                            },
                        )
                    )
                logger.info(
                    f"[ACPProvider] Discovered {len(data.get('agents', []))} "
                    f"agents from {url}"
                )
            except Exception as e:
                logger.warning(
                    f"[ACPProvider] Failed to discover from {url}: {e}"
                )
        return manifests

    async def get_capabilities(
        self, agent_id: str
    ) -> list[Capability]:
        agents = await self.discover_agents()
        for a in agents:
            if a.external_id == agent_id:
                return a.capabilities
        return []

    async def assign_task(
        self, agent_id: str, task: TaskSpec
    ) -> str:
        server_url = self._find_server_for_agent(agent_id)
        if not server_url:
            raise RuntimeError(
                f"No ACP server found for agent '{agent_id}'"
            )

        input_messages = [
            {
                "role": "user",
                "parts": [
                    {
                        "content_type": "text/plain",
                        "content": (
                            f"Task #{task.task_id}: {task.title}\n\n"
                            f"{task.description}\n\n"
                            f"Context: {task.context}"
                        ),
                    }
                ],
            }
        ]

        resp = await self._client.post(
            f"{server_url}/runs",
            json={
                "agent_name": agent_id,
                "input": input_messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        run_id = data["run_id"]
        logger.info(
            f"[ACPProvider] Task #{task.task_id} → "
            f"agent '{agent_id}' → run {run_id[:8]}"
        )
        return run_id

    async def get_status(self, run_id: str) -> RunStatus:
        server_url = self._find_server_for_run(run_id)
        if not server_url:
            return RunStatus(run_id=run_id, status="failed")

        try:
            resp = await self._client.get(
                f"{server_url}/runs/{run_id}"
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "unknown")
            return RunStatus(
                run_id=run_id,
                status="completed"
                if status == "completed"
                else "running" if status == "running"
                else "failed" if status == "failed"
                else "unknown",
                progress=1.0 if status == "completed" else 0.5,
            )
        except Exception as e:
            logger.warning(
                f"[ACPProvider] Status check failed for {run_id[:8]}: {e}"
            )
            return RunStatus(run_id=run_id, status="failed")

    async def collect_results(self, run_id: str) -> TaskResult:
        server_url = self._find_server_for_run(run_id)
        if not server_url:
            return TaskResult(
                run_id=run_id,
                status="failed",
                output={},
                error="Server not found",
            )

        try:
            resp = await self._client.get(
                f"{server_url}/runs/{run_id}"
            )
            resp.raise_for_status()
            data = resp.json()

            output_text = ""
            for msg in data.get("output") or []:
                for part in msg.get("parts") or []:
                    output_text += part.get("content", "")

            return TaskResult(
                run_id=run_id,
                status="completed"
                if data.get("status") == "completed"
                else "failed",
                output={
                    "message": output_text,
                    "files": {},
                    "raw": data,
                },
                error=data.get("error"),
                duration_seconds=2.0,
            )
        except Exception as e:
            logger.warning(
                f"[ACPProvider] Result collection failed for "
                f"{run_id[:8]}: {e}"
            )
            return TaskResult(
                run_id=run_id,
                status="failed",
                output={},
                error=str(e),
            )

    async def cancel_task(self, run_id: str) -> bool:
        return False

    def _find_server_for_agent(self, agent_id: str) -> str | None:
        if self._server_urls:
            return self._server_urls[0]
        return None

    def _find_server_for_run(self, run_id: str) -> str | None:
        if self._server_urls:
            return self._server_urls[0]
        return None
