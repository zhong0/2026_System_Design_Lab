from fastapi import APIRouter, HTTPException
from service.leaderboardSvc import leaderboardSvc
from fastapi.responses import HTMLResponse

router = APIRouter()
leaderboard_service = leaderboardSvc()

@router.get("/leaderboard")
def leaderboard():
    leaderboard_result = leaderboard_service.leaderboard_retrieval()

    if leaderboard_result is None:
        raise HTTPException(status_code=400, detail = { 
            "error_code": "leaderboard-error-1", "error_message": "failed to get leaderboard"})

    return {"leaderboard_table": leaderboard_result}


@router.get('/leaderboard/ui', response_class=HTMLResponse)
def get_leaderboard_ui():
    with open('./frontend/index.html', 'r', encoding='utf-8') as f:
        return f.read()