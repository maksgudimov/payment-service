from app.core.config import Config
from app.infrastructure.base import BaseConnection


class RabbitConnectionClient(BaseConnection):
    def __init__(self, config: Config):
        self._config = config

    @property
    def url(self) -> str:
        return (
            f"amqp://"
            f"{self._config.RABBITMQ_USER}:"
            f"{self._config.RABBITMQ_PASSWORD}@"
            f"{self._config.RABBITMQ_HOST}:"
            f"{self._config.RABBITMQ_PORT}/"
        )
