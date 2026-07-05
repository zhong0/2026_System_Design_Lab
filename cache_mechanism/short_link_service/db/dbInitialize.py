import asyncpg
from config import app_config as config
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

class DBInitialize:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )
            logger.info("Connect to PostgreSQL successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            logger.info("Disconnect to PostgreSQL successfully.")

db_connection = DBInitialize(
    host=config.POSTGRES_IP,
    port=config.POSTGRES_PORT,
    user=config.POSTGRES_USER,
    password=config.POSTGRES_PWD,
    database=config.POSTGRES_DB,
)