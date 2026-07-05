import json
from typing import Awaitable, Callable

from aiokafka import AIOKafkaConsumer

from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


class kafkaConsumer:
    def __init__(self, topic: str, stream_label: str):
        self.topic = topic
        self.stream_label = stream_label
        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=config.KAFKA_BOOTSTRAP,
            group_id=f"event_log_{stream_label}",
            auto_offset_reset="latest",
        )

    async def start(self):
        await self.consumer.start()
        logger.info("Kafka consumer started: topic=%s", self.topic)

    async def stop(self):
        await self.consumer.stop()
        logger.info("Kafka consumer stopped: topic=%s", self.topic)

    async def run(self, broadcast: Callable[[dict], Awaitable[None]]):
        try:
            async for msg in self.consumer:
                try:
                    event = json.loads(msg.value.decode("utf-8"))
                except Exception as e:
                    logger.error("invalid kafka message: %s", e)
                    continue

                envelope = {
                    "stream": self.stream_label,
                    "topic": msg.topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "event": event,
                }
                await broadcast(envelope)
        except Exception as e:
            logger.error("consumer loop error: %s", e)
