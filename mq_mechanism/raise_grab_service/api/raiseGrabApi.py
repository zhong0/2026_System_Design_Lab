import uuid
import socket
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from service.raiseGrabSvc import raiseGrabSvc
from service.syncGrabSvc import syncGrabSvc
from schema.request import GrabRequest
from config import app_config as config

router = APIRouter()
raise_grab_service = raiseGrabSvc()
sync_grab_service = syncGrabSvc()


@router.post("/grab")
async def grab(body: GrabRequest):
    request_id = uuid.uuid4().hex[:12]
    payload = {
        "request_id": request_id,
        "username": body.username,
        "received_at": datetime.now(timezone.utc).isoformat(),
    }

    published = await raise_grab_service.enqueue(payload)
    if not published:
        raise HTTPException(status_code=500, detail={
            "error_code": "grab-error-1",
            "error_message": "failed to enqueue grab request",
        })

    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        ip = "unknown"

    return {
        "status": "queued",
        "request_id": request_id,
        "username": body.username,
        "server_ip": ip,
    }


async def _send_control(action: str, error_code: str):
    payload = {
        "action": action,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    published = await raise_grab_service.control(payload, config.RABBITMQ_CONTROL_QUEUE)
    if not published:
        raise HTTPException(status_code=500, detail={
            "error_code": error_code,
            "error_message": f"failed to publish {action}",
        })
    return {"status": f"{action}_queued"}


@router.post("/reset")
async def reset():
    await sync_grab_service.reset()
    return await _send_control("reset", "reset-error-1")


@router.post("/control/pause")
async def pause():
    return await _send_control("pause", "pause-error-1")


@router.post("/control/resume")
async def resume():
    return await _send_control("resume", "resume-error-1")


@router.post("/grab-sync")
async def grab_sync(body: GrabRequest):
    request_id = uuid.uuid4().hex[:12]
    return await sync_grab_service.grab(body.username, request_id)


@router.post("/reset-sync")
async def reset_sync():
    return await sync_grab_service.reset()


@router.get("/sync/state")
async def sync_state():
    return sync_grab_service.state()
