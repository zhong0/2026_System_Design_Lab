from fastapi import APIRouter
from api.shortLinksApi import router as short_link_router

router = APIRouter()
router.include_router(short_link_router, tags=["Short Link"])