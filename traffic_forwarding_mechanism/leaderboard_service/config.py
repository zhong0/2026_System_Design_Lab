from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    APP_NAME: str
    SERVER_IP: str = ""
    SERVER_PORT: int = 1001
    REDIS_IP: str = "localhost"
    REDIS_PORT: int = 6379
    CODE_ROOT: str = "/app"

app_config = AppConfig()