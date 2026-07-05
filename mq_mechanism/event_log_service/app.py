import time
import uuid
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from api.router import router
from kafka_tool.kafkaConsumer import kafkaConsumer
from service.wsManager import ws_manager
from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("System starts.")

    consumer_requests = kafkaConsumer(
        topic=config.KAFKA_TOPIC_REQUESTS, stream_label="requests",
    )
    consumer_results = kafkaConsumer(
        topic=config.KAFKA_TOPIC_RESULTS, stream_label="results",
    )
    await consumer_requests.start()
    await consumer_results.start()

    task_requests = asyncio.create_task(consumer_requests.run(ws_manager.broadcast))
    task_results = asyncio.create_task(consumer_results.run(ws_manager.broadcast))

    try:
        yield
    finally:
        task_requests.cancel()
        task_results.cancel()
        await consumer_requests.stop()
        await consumer_results.stop()
        logger.info("System ends.")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    rid = uuid.uuid4().hex[:8]
    path = request.url.path
    logger.info("rid=%s path=%s start request", rid, path)

    start_time = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "rid=%s path=%s completed_in=%.2fms status_code=%d",
        rid, path, elapsed_ms, response.status_code,
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": detail.get("error_code", exc.status_code),
            "error_message": detail.get("error_message", exc.detail),
        },
    )


app.include_router(router, prefix="")
