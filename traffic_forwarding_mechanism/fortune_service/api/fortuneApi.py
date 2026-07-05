from fastapi import APIRouter, HTTPException
from service.fortune import fortuneSvc
from schema.request import FortuneRequest
import socket

router = APIRouter()
fortune_service = fortuneSvc()

@router.post("/fortune")
def fortune(body: FortuneRequest):
    fortune_result = fortune_service.random_draw(body.username)

    if not fortune_result:
        raise HTTPException(status_code=400, detail = { 
            "error_code": "fortune-error-1", "error_message": "failed to save fortune"})

    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    return {
        "username": body.username,
        "fortune": fortune_result,
        "server_ip": ip
    }