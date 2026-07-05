import asyncpg
from db.dbInitialize import db_connection
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

class shortLinksDao:
    async def create(self, code: str, original_url: str):
        try:
            async with db_connection.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO short_links (code, original_url)
                    VALUES ($1, $2)
                    """,
                    code, original_url
                )
                logger.info(f"Created short link: {code}")
                return True
        except asyncpg.UniqueViolationError:
            logger.error(f"Code already exists: {code}")
            return False
        except Exception as e:
            logger.error(f"Failed to create short link: {str(e)}")
            return False

    async def get_by_code(self, code: str):
        try:
            async with db_connection.pool.acquire() as conn:
                return await conn.fetchrow(
                    """
                    SELECT * FROM short_links 
                    WHERE code = $1 
                    AND (expires_at IS NULL OR expires_at > NOW())
                    """,
                    code
                )
        except Exception as e:
            logger.error(f"Failed to get short link: {str(e)}")
            return None

    async def delete(self, code: str):
        try:
            async with db_connection.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM short_links WHERE code = $1",
                    code
                )
                logger.info(f"Deleted short link: {code}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete short link: {str(e)}")
            return False

short_link_dao = shortLinksDao()