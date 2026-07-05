from fastapi import APIRouter
from api.eventLogApi import router as event_log_router

router = APIRouter()
router.include_router(event_log_router, tags=["event_log"])
