import json
import aio_pika

from mq_tool.rabbitmqInitialize import rabbitmq_connection
from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


class rabbitmqPublisher:
    async def publish(self, payload: dict, queue: str | None = None) -> bool:
        try:
            channel = rabbitmq_connection.channel
            if channel is None:
                logger.error("RabbitMQ channel not initialized")
                return False

            routing_key = queue or config.RABBITMQ_QUEUE
            message = aio_pika.Message(
                body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                content_type="application/json",
            )
            await channel.default_exchange.publish(message, routing_key=routing_key)
            logger.info("published to %s: %s", routing_key, payload.get("request_id") or payload.get("action"))
            return True
        except Exception as e:
            logger.error(e)
            return False
