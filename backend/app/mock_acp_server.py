"""
Mock ACP (Agent Communication Protocol) server for local development.

Implements the ACP wire protocol:
  GET  /agents       → list available agents
  POST /runs         → start a run (async simulation)
  GET  /runs/{id}    → get run status / result

Run standalone:
  python -m app.mock_acp_server

Or programmatically (for testing):
  from app.mock_acp_server import start_mock_server
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mock_acp")

MOCK_AGENTS = [
    {
        "name": "backend_dev",
        "description": "Builds APIs, models, and backend logic",
        "metadata": {
            "capabilities": ["backend", "python", "api", "database"],
            "cost": 6,
            "speed": 7,
            "quality": 8,
        },
    },
    {
        "name": "frontend_dev",
        "description": "Creates UI components and responsive layouts",
        "metadata": {
            "capabilities": ["frontend", "typescript", "css", "ui"],
            "cost": 5,
            "speed": 8,
            "quality": 7,
        },
    },
    {
        "name": "writer",
        "description": "Writes documentation, copy, and narrative content",
        "metadata": {
            "capabilities": ["writing", "documentation", "content"],
            "cost": 3,
            "speed": 9,
            "quality": 8,
        },
    },
]

MOCK_AGENT_MAP = {a["name"]: a for a in MOCK_AGENTS}

_runs: dict[str, dict] = {}
_work_delay: float = 2.0

app = FastAPI(title="Mock ACP Server", version="0.1.0")


class RunRequest(BaseModel):
    agent_name: str
    input: list[dict] = []


class RunResponse(BaseModel):
    run_id: str
    agent_name: str
    session_id: str | None = None
    status: str
    output: list | None = None
    error: str | None = None


@app.get("/agents")
def list_agents():
    return {"agents": MOCK_AGENTS}


@app.post("/runs", status_code=201)
async def create_run(body: RunRequest):
    if body.agent_name not in MOCK_AGENT_MAP:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{body.agent_name}' not found",
        )

    run_id = str(uuid.uuid4())
    _runs[run_id] = {
        "run_id": run_id,
        "agent_name": body.agent_name,
        "status": "running",
        "input": body.input,
        "output": None,
        "error": None,
        "started_at": asyncio.get_event_loop().time(),
    }

    asyncio.create_task(_simulate_work(run_id))

    return RunResponse(
        run_id=run_id,
        agent_name=body.agent_name,
        status="running",
    )


@app.get("/runs/{run_id}")
def get_run(run_id: str):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse(
        run_id=run["run_id"],
        agent_name=run["agent_name"],
        status=run["status"],
        output=run.get("output"),
        error=run.get("error"),
    )


async def _simulate_work(run_id: str):
    run = _runs[run_id]
    await asyncio.sleep(_work_delay)
    agent = MOCK_AGENT_MAP.get(run["agent_name"])
    run["status"] = "completed"
    run["output"] = [
        {
            "role": f"agent/{run['agent_name']}",
            "parts": [
                {
                    "content_type": "text/plain",
                    "content": (
                        f"[Mock ACP] {agent['name']} completed run {run_id[:8]}.\n"
                        f"Task: mock execution\n"
                        f"Result: simulation successful"
                    ),
                }
            ],
        }
    ]
    logger.info(f"Run {run_id[:8]} completed: {run['agent_name']}")


def start_mock_server(host: str = "0.0.0.0", port: int = 9001):
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001, log_level="info")
