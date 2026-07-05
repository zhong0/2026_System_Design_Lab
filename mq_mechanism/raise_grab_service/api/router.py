from fastapi import APIRouter
from api.raiseGrabApi import router as raise_grab_router

router = APIRouter()
router.include_router(raise_grab_router, tags=["raise_grab"])
