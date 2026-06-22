import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.config import settings
from app.kernel.event_bus import event_bus
from app.kernel.log_handler import WebSocketLogHandler
from app.api import projects, organizations, tasks, websocket, generation, memory, reviews, git, pipeline, integration

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("studioos")

ws_handler = WebSocketLogHandler(event_bus)
ws_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logging.getLogger("studioos").addHandler(ws_handler)
logging.getLogger("studioos.projects").addHandler(ws_handler)
logging.getLogger("studioos.generation").addHandler(ws_handler)
logging.getLogger("studioos.tasks").addHandler(ws_handler)
logging.getLogger("studioos.file_manager").addHandler(ws_handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.output_dir, exist_ok=True)
    init_db()
    logger.info(f"StudioOS v{app.version} started (env={settings.environment})")
    yield


app = FastAPI(title="StudioOS", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(organizations.router)
app.include_router(tasks.router)
app.include_router(websocket.router)
app.include_router(generation.router)
app.include_router(memory.router)
app.include_router(reviews.router)
app.include_router(git.router)
app.include_router(pipeline.router)
app.include_router(integration.router)

output_abs = os.path.abspath(settings.output_dir)
os.makedirs(output_abs, exist_ok=True)
app.mount("/output", StaticFiles(directory=output_abs), name="output")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": app.version,
        "environment": settings.environment,
    }
