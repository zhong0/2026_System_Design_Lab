import json
from confluent_kafka import Producer

from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


class kafkaProducer:
    def __init__(self):
        self.producer = Producer({
            "bootstrap.servers": config.KAFKA_BOOTSTRAP,
            "client.id": "grab_worker",
        })

    def publish(self, topic: str, payload: dict) -> bool:
        try:
            self.producer.produce(
                topic=topic,
                value=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                callback=self._delivery_report,
            )
            self.producer.poll(0)
            return True
        except Exception as e:
            logger.error("kafka publish error: %s", e)
            return False

    def _delivery_report(self, err, msg):
        if err is not None:
            logger.error("kafka delivery failed: %s", err)
        else:
            logger.info(
                "kafka delivered to %s [partition=%d offset=%d]",
                msg.topic(), msg.partition(), msg.offset(),
            )
