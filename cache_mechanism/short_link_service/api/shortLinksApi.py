from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from config import app_config as config
from service.shortLinksSvc import shortLinksSvc
from schema.request import createLinkRequest
import socket

router = APIRouter()
short_links_service = shortLinksSvc()

@router.get('/static/ui', response_class=HTMLResponse)
async def get_ui():
    with open('./frontend/index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    html = html.replace('__CACHE_TTL__', str(config.CACHE_TTL))
    return html

@router.post("/create_short_link")
async def create_short_link(body: createLinkRequest):
    create_code = await short_links_service.create_short_link(body.urlLink)

    if create_code is None:
        raise HTTPException(status_code=400, detail = { 
            "error_code": "sl-error-1", "error_message": "failed to create short link"})

    return {
        "short_link": f"http://{config.SERVER_IP}:{config.SERVER_PORT}/{create_code}"
    }

@router.get('/link/{code}/info')
async def get_link_info(code: str):
    response = await short_links_service.get_link_info(code)
    if response is None:
        raise HTTPException(status_code=400, detail={
            "error_code": "sl-error-2", "error_message": "short link is invalid"})
    return response

@router.get("/{code}")
async def get_short_link(code: str):
    original_url = await short_links_service.get_short_link(code)

    if original_url is None:
        raise HTTPException(status_code=404, detail={
            "error_code": "sl-error-2", "error_message": "short link is invalid"})

    return RedirectResponse(url=original_url)