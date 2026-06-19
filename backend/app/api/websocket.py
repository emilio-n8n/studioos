import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.kernel.event_bus import event_bus

logger = logging.getLogger("studioos.websocket")
router = APIRouter()

MAX_WS_PER_PROJECT = 50


@router.websocket("/ws/projects/{project_id}")
async def project_websocket(project_id: int, ws: WebSocket):
    current_count = len(event_bus._websockets.get(project_id, []))
    if current_count >= MAX_WS_PER_PROJECT:
        await ws.close(code=1013, reason="Too many connections")
        return

    await ws.accept()
    event_bus.register_ws(project_id, ws)
    try:
        while True:
            try:
                await ws.receive_text()
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.warning(f"WebSocket receive error: {e}")
                break
    except Exception as e:
        logger.warning(f"WebSocket error for project {project_id}: {e}")
    finally:
        event_bus.unregister_ws(project_id, ws)
