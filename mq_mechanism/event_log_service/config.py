from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    APP_NAME: str
    SERVER_IP: str = ""
    SERVER_PORT: int = 1003
    KAFKA_BOOTSTRAP: str = "kafka:9092"
    KAFKA_TOPIC_REQUESTS: str = "grab_requests_log"
    KAFKA_TOPIC_RESULTS: str = "grab_results_log"
    CODE_ROOT: str = "/app"


app_config = AppConfig()
