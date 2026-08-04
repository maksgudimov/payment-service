from faststream.rabbit import RabbitExchange, RabbitQueue
from faststream.rabbit.schemas import QueueType


PAYMENTS_ROUTING_KEY = "payments.new"
PAYMENTS_FAILED_ROUTING_KEY = "payments.failed"

PAYMENTS_EXCHANGE = RabbitExchange("payments", durable=True)
PAYMENTS_DLX = RabbitExchange("payments.dlx", durable=True)

PAYMENTS_NEW_QUEUE = RabbitQueue(
    "payments.new",
    queue_type=QueueType.QUORUM,
    durable=True,
    routing_key=PAYMENTS_ROUTING_KEY,
    arguments={
        "x-delivery-limit": 3,
        "x-dead-letter-exchange": PAYMENTS_DLX.name,
        "x-dead-letter-routing-key": PAYMENTS_FAILED_ROUTING_KEY,
        "x-dead-letter-strategy": "at-least-once",
        "x-overflow": "reject-publish",
    },
)

PAYMENTS_DLQ = RabbitQueue(
    "payments.dlq",
    queue_type=QueueType.QUORUM,
    durable=True,
    routing_key=PAYMENTS_FAILED_ROUTING_KEY,
)
