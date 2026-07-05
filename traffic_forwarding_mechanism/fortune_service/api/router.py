from fastapi import APIRouter
from api.fortuneApi import router as fortune_router

router = APIRouter()
router.include_router(fortune_router, tags=["fortune"])