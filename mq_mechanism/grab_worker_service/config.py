from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    APP_NAME: str
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_QUEUE: str = "grab_requests"
    RABBITMQ_CONTROL_QUEUE: str = "grab_control"
    KAFKA_BOOTSTRAP: str = "kafka:9092"
    KAFKA_TOPIC_REQUESTS: str = "grab_requests_log"
    KAFKA_TOPIC_RESULTS: str = "grab_results_log"
    TOTAL_SPOTS: int = 3
    PROCESS_DELAY_MS: int = 300
    CODE_ROOT: str = "/app"


app_config = AppConfig()
