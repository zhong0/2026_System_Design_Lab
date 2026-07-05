from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    APP_NAME: str
    SERVER_IP: str = ""
    SERVER_PORT: int = 1002
    REDIS_IP: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PWD: str = ""
    CODE_ROOT: str = "/app"
    POSTGRES_IP: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "erin"
    POSTGRES_PWD: str = ""
    POSTGRES_DB: str = "cachelab"
    CACHE_TTL: int = 3600
    
app_config = AppConfig()