import json
import threading
import time
from datetime import datetime, timezone

import pika
from pika.exceptions import AMQPConnectionError

from kafka_tool.kafkaProducer import kafkaProducer
from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


class grabWorker:
    def __init__(self):
        self.producer = kafkaProducer()
        self.spots_remaining = config.TOTAL_SPOTS
        self.delay_sec = config.PROCESS_DELAY_MS / 1000.0

        self.resume_event = threading.Event()
        self.resume_event.set()
        self.main_connection = None
        self.main_channel = None
        self.main_consumer_tag = None

    def run(self):
        threading.Thread(target=self._run_control_consumer, daemon=True).start()
        self._run_main_consumer()

    def _conn(self):
        return pika.BlockingConnection(
            pika.ConnectionParameters(host=config.RABBITMQ_HOST, port=config.RABBITMQ_PORT)
        )

    # ---------- main grab consumer ----------
    def _run_main_consumer(self):
        while True:
            try:
                self.main_connection = self._conn()
                self.main_channel = self.main_connection.channel()
                self.main_channel.queue_declare(queue=config.RABBITMQ_QUEUE, durable=False)
                self.main_channel.basic_qos(prefetch_count=1)

                while True:
                    self.resume_event.wait()
                    self.main_consumer_tag = self.main_channel.basic_consume(
                        queue=config.RABBITMQ_QUEUE,
                        on_message_callback=self._on_grab_message,
                    )
                    logger.info("main consumer subscribed tag=%s", self.main_consumer_tag)
                    self.main_channel.start_consuming()
                    self.main_consumer_tag = None
                    logger.info("main consumer paused")
            except AMQPConnectionError as e:
                logger.error("main conn lost, retry in 3s: %s", e)
                self.main_connection = None
                self.main_channel = None
                self.main_consumer_tag = None
                time.sleep(3)

    def _on_grab_message(self, ch, method, _props, body):
        try:
            self._handle_grab(json.loads(body))
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error("handler error: %s", e)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def _handle_grab(self, data):
        username = data.get("username")
        request_id = data.get("request_id")

        self.producer.publish(config.KAFKA_TOPIC_REQUESTS, {
            "event_type": "grab_received",
            "request_id": request_id,
            "username": username,
            "ts": datetime.now(timezone.utc).isoformat(),
        })

        time.sleep(self.delay_sec)

        if self.spots_remaining > 0:
            self.spots_remaining -= 1
            spot = config.TOTAL_SPOTS - self.spots_remaining
            result = {
                "event_type": "grab_won",
                "request_id": request_id,
                "username": username,
                "spot": spot,
                "spots_remaining": self.spots_remaining,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            logger.info("%s won spot %d (remaining=%d)", username, spot, self.spots_remaining)
        else:
            result = {
                "event_type": "grab_lost",
                "request_id": request_id,
                "username": username,
                "reason": "no_spots",
                "ts": datetime.now(timezone.utc).isoformat(),
            }
            logger.info("%s lost (no spots)", username)

        self.producer.publish(config.KAFKA_TOPIC_RESULTS, result)

    # ---------- control consumer ----------
    def _run_control_consumer(self):
        while True:
            try:
                conn = self._conn()
                ch = conn.channel()
                ch.queue_declare(queue=config.RABBITMQ_CONTROL_QUEUE, durable=False)
                ch.basic_qos(prefetch_count=1)

                def _on_control(c, method, _props, body):
                    try:
                        self._handle_control(json.loads(body))
                        c.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        logger.error("control handler error: %s", e)
                        c.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                ch.basic_consume(queue=config.RABBITMQ_CONTROL_QUEUE, on_message_callback=_on_control)
                logger.info("control consumer started on %s", config.RABBITMQ_CONTROL_QUEUE)
                ch.start_consuming()
            except AMQPConnectionError as e:
                logger.error("control conn lost, retry in 3s: %s", e)
                time.sleep(3)

    def _handle_control(self, data):
        action = data.get("action")

        if action == "pause":
            self.resume_event.clear()
            tag = self.main_consumer_tag
            conn = self.main_connection
            ch = self.main_channel
            if conn and ch and tag:
                conn.add_callback_threadsafe(lambda: ch.basic_cancel(tag))
            self.producer.publish(config.KAFKA_TOPIC_RESULTS, {
                "event_type": "worker_paused",
                "ts": datetime.now(timezone.utc).isoformat(),
            })
            logger.info("worker paused")

        elif action == "resume":
            self.resume_event.set()
            self.producer.publish(config.KAFKA_TOPIC_RESULTS, {
                "event_type": "worker_resumed",
                "ts": datetime.now(timezone.utc).isoformat(),
            })
            logger.info("worker resumed")

        elif action == "reset":
            self.spots_remaining = config.TOTAL_SPOTS
            self.producer.publish(config.KAFKA_TOPIC_RESULTS, {
                "event_type": "reset",
                "spots_remaining": config.TOTAL_SPOTS,
                "ts": datetime.now(timezone.utc).isoformat(),
            })
            logger.info("spots reset to %d", config.TOTAL_SPOTS)

        else:
            logger.warning("unknown control action: %s", action)
