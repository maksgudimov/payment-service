from faststream.rabbit import RabbitBroker

from app.core.config import config
from app.infrastructure.broker.connection import RabbitConnectionClient


rabbitmq = RabbitBroker(RabbitConnectionClient(config).url)
