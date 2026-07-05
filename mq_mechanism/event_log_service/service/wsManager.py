import json
import asyncio

from fastapi import WebSocket
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


class wsManager:
    def __init__(self):
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self.mode: str = "async"

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
        logger.info("ws client connected, total=%d", len(self._clients))
        try:
            await websocket.send_text(json.dumps({"type": "mode", "mode": self.mode}))
        except Exception as e:
            logger.error("ws initial mode send error: %s", e)

    async def set_mode(self, mode: str):
        if mode not in ("async", "sync"):
            return
        self.mode = mode
        await self.broadcast({"type": "mode", "mode": mode})
        logger.info("mode broadcast: %s", mode)

    def disconnect(self, websocket: WebSocket):
        self._clients.discard(websocket)
        logger.info("ws client disconnected, total=%d", len(self._clients))

    async def broadcast(self, message: dict):
        if not self._clients:
            return
        payload = json.dumps(message, ensure_ascii=False)
        dead: list[WebSocket] = []
        for ws in list(self._clients):
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.error("ws send error: %s", e)
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)


ws_manager = wsManager()
