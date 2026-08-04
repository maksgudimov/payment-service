import os
from dotenv import load_dotenv


load_dotenv()


class Config:
    def __init__(self) -> None:
        self.POSTGRES_HOST = os.getenv("POSTGRES_HOST")
        self.POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
        self.POSTGRES_DB = os.getenv("POSTGRES_DB")
        self.POSTGRES_USER = os.getenv("POSTGRES_USER")
        self.POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        self.DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
        self.DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))

        self.RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
        self.RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
        self.RABBITMQ_USER = os.getenv("RABBITMQ_USER")
        self.RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
        self.RABBITMQ_MANAGEMENT_PORT = int(
            os.getenv("RABBITMQ_MANAGEMENT_PORT", 15672)
        )

        self.REDIS_HOST = os.getenv("REDIS_HOST")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        self.REDIS_DB = int(os.getenv("REDIS_DB", 0))
        self.IDEMPOTENCY_LOCK_TTL_SECONDS = int(
            os.getenv("IDEMPOTENCY_LOCK_TTL_SECONDS", "30")
        )

        self.OUTBOX_POLL_INTERVAL_SECONDS = float(
            os.getenv("OUTBOX_POLL_INTERVAL_SECONDS", "1")
        )
        self.OUTBOX_BATCH_SIZE = int(os.getenv("OUTBOX_BATCH_SIZE", "100"))
        self.WEBHOOK_TIMEOUT_SECONDS = float(
            os.getenv("WEBHOOK_TIMEOUT_SECONDS", "5")
        )
        self.WEBHOOK_RETRY_ATTEMPTS = int(
            os.getenv("WEBHOOK_RETRY_ATTEMPTS", "3")
        )
        self.WEBHOOK_RETRY_BASE_DELAY_SECONDS = float(
            os.getenv("WEBHOOK_RETRY_BASE_DELAY_SECONDS", "1")
        )
        self.PAYMENT_PROCESSING_MIN_SECONDS = float(
            os.getenv("PAYMENT_PROCESSING_MIN_SECONDS", "2")
        )
        self.PAYMENT_PROCESSING_MAX_SECONDS = float(
            os.getenv("PAYMENT_PROCESSING_MAX_SECONDS", "5")
        )
        self.HEALTHCHECK_TIMEOUT_SECONDS = float(
            os.getenv("HEALTHCHECK_TIMEOUT_SECONDS", "2")
        )

        self.APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
        self.APP_PORT = int(os.getenv("APP_PORT", 8000))
        self.APP_WORKERS = int(os.getenv("APP_WORKERS", 1))
        self.API_KEY = os.getenv("API_KEY", "")


config = Config()
