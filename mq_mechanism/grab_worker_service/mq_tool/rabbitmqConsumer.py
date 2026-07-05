import time
import pika
from pika.exceptions import AMQPConnectionError

from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


class rabbitmqConsumer:
    def __init__(self):
        self.host = config.RABBITMQ_HOST
        self.port = config.RABBITMQ_PORT
        self.queue = config.RABBITMQ_QUEUE

    def _connect(self):
        params = pika.ConnectionParameters(host=self.host, port=self.port)
        return pika.BlockingConnection(params)

    def consume(self, handler):
        while True:
            try:
                connection = self._connect()
                channel = connection.channel()
                channel.queue_declare(queue=self.queue, durable=False)
                channel.basic_qos(prefetch_count=1)

                def _on_message(ch, method, _props, body):
                    try:
                        handler(body)
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as e:
                        logger.error("handler error: %s", e)
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

                channel.basic_consume(queue=self.queue, on_message_callback=_on_message)
                logger.info("Worker started consuming queue=%s", self.queue)
                channel.start_consuming()
            except AMQPConnectionError as e:
                logger.error("RabbitMQ connection lost, retrying in 3s: %s", e)
                time.sleep(3)
