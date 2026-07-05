from fastapi import APIRouter
from api.leaderboardApi import router as leaderboard_router

router = APIRouter()
router.include_router(leaderboard_router, tags=["fortune"])