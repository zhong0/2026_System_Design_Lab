from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    APP_NAME: str
    SERVER_IP: str = ""
    SERVER_PORT: int = 1001
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_QUEUE: str = "grab_requests"
    RABBITMQ_CONTROL_QUEUE: str = "grab_control"
    TOTAL_SPOTS: int = 3
    SYNC_DELAY_MS: int = 1500
    CODE_ROOT: str = "/app"


app_config = AppConfig()
