from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from service.wsManager import ws_manager

router = APIRouter()


class ModeBody(BaseModel):
    mode: str


@router.get("/", response_class=HTMLResponse)
def serve_grab():
    with open("./frontend/grab.html", "r", encoding="utf-8") as f:
        return f.read()


@router.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    with open("./frontend/index.html", "r", encoding="utf-8") as f:
        return f.read()


@router.get("/mode")
def get_mode():
    return {"mode": ws_manager.mode}


@router.post("/mode")
async def set_mode(body: ModeBody):
    if body.mode not in ("async", "sync"):
        raise HTTPException(status_code=400, detail="mode must be async or sync")
    await ws_manager.set_mode(body.mode)
    return {"mode": ws_manager.mode}


@router.websocket("/ws")
async def websocket_events(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
