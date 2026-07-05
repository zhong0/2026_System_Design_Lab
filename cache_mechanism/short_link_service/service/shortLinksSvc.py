import random
import string
import time
from dao.shortLinksDao import shortLinksDao
from cache.cacheOperation import cacheOperation
from log.logTemplate import JSONLogger

logger = JSONLogger(__name__).get_logger()

class shortLinksSvc:
    def __init__(self):
       self.short_links_dao = shortLinksDao()
       self.cache_op = cacheOperation()
    
    def generate_code(self, length: int = 6) -> str:
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=length))
    
    async def create_short_link(self, link):
        code = self.generate_code(6)
        while await self.short_links_dao.get_by_code(code) is not None:
            code = self.generate_code(6)
        insert_result = await self.short_links_dao.create(code, link)
        if not insert_result:
            return None
        await self.cache_op.set(code, link)
        return code
    
    async def get_short_link(self, code):
        cached_url = await self.cache_op.get(code)
        if cached_url:
            logger.info(f"Cache hit for code: {code}")
            return cached_url
    
        get_result = await self.short_links_dao.get_by_code(code)

        if get_result is None:
            return None
        
        logger.info(f"Cache miss for code: {code}")

        await self.cache_op.set(code, get_result['original_url'])
        return get_result['original_url']
    
    async def get_link_info(self, code):
        start = time.perf_counter()
        cached_url = await self.cache_op.get(code)
        if cached_url:
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(f"Cache hit for code: {code} | elapsed: {elapsed:.2f}ms")
            return { "url": cached_url, "source": "redis", "excuted_time": f"{elapsed:.2f}"} 
    
        get_result = await self.short_links_dao.get_by_code(code)

        if get_result is None:
            return None
        
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(f"Cache miss for code: {code} | elapsed: {elapsed:.2f}ms")

        await self.cache_op.set(code, get_result['original_url'])
        return { "url": get_result['original_url'], "source": "postgres", "excuted_time": f"{elapsed:.2f}"}


