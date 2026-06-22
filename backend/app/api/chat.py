"""Chat with CEO — streaming SSE endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.database import get_db
from app.models.project import Project
from app.workforce.ceo_agent import chat_stream

logger = logging.getLogger("studioos.chat")
router = APIRouter(prefix="/api/projects/{project_id}/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


@router.post("")
async def chat_with_ceo(project_id: int, body: ChatRequest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    api_key = project.openai_api_key or ""
    provider = project.provider or "openai"
    model = project.model or None

    async def event_stream():
        async for event in chat_stream(
            project_id=project_id,
            message=body.message,
            history=[m.model_dump() for m in body.history],
            api_key=api_key,
            provider=provider,
            model=model,
            db=db,
        ):
            yield f"data: {event}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
