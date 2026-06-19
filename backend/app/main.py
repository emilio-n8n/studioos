import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.config import settings
from app.api import projects, organizations, tasks, websocket, generation

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger("studioos")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.output_dir, exist_ok=True)
    init_db()
    logger.info(f"StudioOS v{app.version} started (env={settings.environment})")
    yield


app = FastAPI(title="StudioOS", version="0.3.0", lifespan=lifespan)

cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
allow_creds = "*" not in cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if not allow_creds else ["*"],
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(organizations.router)
app.include_router(tasks.router)
app.include_router(websocket.router)
app.include_router(generation.router)

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
