import asyncio
from datetime import datetime, timezone

from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


class syncGrabSvc:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.delay_sec = config.SYNC_DELAY_MS / 1000.0
        self.spots = [None] * config.TOTAL_SPOTS
        self.reset_ts = datetime.now(timezone.utc).isoformat()

    async def grab(self, username: str, request_id: str) -> dict:
        enqueue_ts = datetime.now(timezone.utc).isoformat()
        async with self.lock:
            start_ts = datetime.now(timezone.utc).isoformat()
            await asyncio.sleep(self.delay_sec)

            for i in range(len(self.spots)):
                if self.spots[i] is None:
                    self.spots[i] = {"username": username, "request_id": request_id, "ts": start_ts}
                    finish_ts = datetime.now(timezone.utc).isoformat()
                    logger.info("[sync] %s won spot %d", username, i + 1)
                    return {
                        "result": "won",
                        "spot": i + 1,
                        "username": username,
                        "request_id": request_id,
                        "enqueue_ts": enqueue_ts,
                        "start_ts": start_ts,
                        "finish_ts": finish_ts,
                    }

            finish_ts = datetime.now(timezone.utc).isoformat()
            logger.info("[sync] %s lost (no spots)", username)
            return {
                "result": "lost",
                "reason": "no_spots",
                "username": username,
                "request_id": request_id,
                "enqueue_ts": enqueue_ts,
                "start_ts": start_ts,
                "finish_ts": finish_ts,
            }

    async def reset(self) -> dict:
        async with self.lock:
            self.spots = [None] * config.TOTAL_SPOTS
            self.reset_ts = datetime.now(timezone.utc).isoformat()
            logger.info("[sync] spots reset")
            return {"status": "reset", "ts": self.reset_ts}

    def state(self) -> dict:
        return {
            "spots": [
                {"index": i + 1, "username": s["username"] if s else None}
                for i, s in enumerate(self.spots)
            ],
            "remaining": sum(1 for s in self.spots if s is None),
            "reset_ts": self.reset_ts,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
