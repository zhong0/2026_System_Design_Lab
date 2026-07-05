import aio_pika

from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()


class rabbitmqInitialize:
    def __init__(self, host: str, port: int, queue: str):
        self.host = host
        self.port = port
        self.queue = queue
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.RobustChannel | None = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.host, port=self.port,
            )
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(self.queue, durable=False)
            await self.channel.declare_queue(config.RABBITMQ_CONTROL_QUEUE, durable=False)
            logger.info("Connect to RabbitMQ successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")

    async def disconnect(self):
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("Disconnect from RabbitMQ.")


rabbitmq_connection = rabbitmqInitialize(
    config.RABBITMQ_HOST, config.RABBITMQ_PORT, config.RABBITMQ_QUEUE,
)
