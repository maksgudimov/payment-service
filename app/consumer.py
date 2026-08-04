import asyncio
from functools import partial

import structlog
from faststream import FastStream
from faststream.exceptions import RejectMessage
from faststream.middlewares import AckPolicy

from app.application.payments import PaymentProcessor
from app.core.config import config
from app.infrastructure.broker.broker import rabbitmq
from app.infrastructure.broker.topology import (
    PAYMENTS_DLQ,
    PAYMENTS_DLX,
    PAYMENTS_EXCHANGE,
    PAYMENTS_FAILED_ROUTING_KEY,
    PAYMENTS_NEW_QUEUE,
)
from app.infrastructure.db.database import database
from app.infrastructure.http import AioHttpWebhookClient
from app.infrastructure.payment_gateway import SimulatedPaymentGateway
from app.infrastructure.uow import SQLAlchemyPaymentUnitOfWork
from app.messaging.schemas import PaymentCreatedMessage


logger = structlog.get_logger(__name__)
webhook_client = AioHttpWebhookClient(config)
payment_gateway = SimulatedPaymentGateway(config)
app = FastStream(rabbitmq)


@rabbitmq.subscriber(
    PAYMENTS_NEW_QUEUE,
    PAYMENTS_EXCHANGE,
    ack_policy=AckPolicy.REJECT_ON_ERROR,
)
async def consume_payment_created(event: PaymentCreatedMessage) -> None:
    try:
        await process_payment_created(event)
    except Exception as error:
        logger.exception(
            "Payment message processing failed; scheduling redelivery",
            payment_id=str(event.payment_id),
        )
        raise RejectMessage(requeue=True) from error


async def process_payment_created(event: PaymentCreatedMessage) -> None:
    async for session in database.session():
        processor = PaymentProcessor(
            partial(SQLAlchemyPaymentUnitOfWork, session),
            payment_gateway,
            webhook_client,
        )
        await processor.execute(event.payment_id)
        logger.info("Payment message processed", payment_id=str(event.payment_id))
        return


@app.on_startup
async def setup_consumer() -> None:
    database.connect()
    await database.ping()
    await webhook_client.start()

    await rabbitmq.connect()
    dead_letter_exchange = await rabbitmq.declare_exchange(PAYMENTS_DLX)
    dead_letter_queue = await rabbitmq.declare_queue(PAYMENTS_DLQ)
    await dead_letter_queue.bind(
        dead_letter_exchange,
        routing_key=PAYMENTS_FAILED_ROUTING_KEY,
    )


@app.on_shutdown
async def shutdown_consumer() -> None:
    await webhook_client.close()
    await database.disconnect()


if __name__ == "__main__":
    asyncio.run(app.run())
