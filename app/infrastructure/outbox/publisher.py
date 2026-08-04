import asyncio
from datetime import datetime, timezone

import structlog
from faststream.rabbit import RabbitBroker
from sqlalchemy import select

from app.common.enums import OutboxStatus
from app.core.config import Config
from app.infrastructure.broker.topology import (
    PAYMENTS_DLQ,
    PAYMENTS_DLX,
    PAYMENTS_EXCHANGE,
    PAYMENTS_FAILED_ROUTING_KEY,
    PAYMENTS_NEW_QUEUE,
    PAYMENTS_ROUTING_KEY,
)
from app.infrastructure.db.connection import PostgresConnectionClient
from app.models.outbox import OutboxMessage


logger = structlog.get_logger(__name__)


class OutboxPublisher:
    def __init__(
        self,
        database: PostgresConnectionClient,
        broker: RabbitBroker,
        config: Config,
    ) -> None:
        self._database = database
        self._broker = broker
        self._poll_interval = config.OUTBOX_POLL_INTERVAL_SECONDS
        self._batch_size = config.OUTBOX_BATCH_SIZE
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        payments_exchange = await self._broker.declare_exchange(PAYMENTS_EXCHANGE)
        payments_queue = await self._broker.declare_queue(PAYMENTS_NEW_QUEUE)
        await payments_queue.bind(
            payments_exchange,
            routing_key=PAYMENTS_ROUTING_KEY,
        )

        dead_letter_exchange = await self._broker.declare_exchange(PAYMENTS_DLX)
        dead_letter_queue = await self._broker.declare_queue(PAYMENTS_DLQ)
        await dead_letter_queue.bind(
            dead_letter_exchange,
            routing_key=PAYMENTS_FAILED_ROUTING_KEY,
        )
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="outbox-publisher")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                published = await self.publish_batch()
            except Exception:
                logger.exception("Outbox publishing iteration failed")
                published = 0

            if published == 0:
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._poll_interval,
                    )
                except TimeoutError:
                    pass

    async def publish_batch(self) -> int:
        async for session in self._database.session():
            messages = list(
                await session.scalars(
                    select(OutboxMessage)
                    .where(OutboxMessage.status == OutboxStatus.PENDING)
                    .order_by(OutboxMessage.created_at)
                    .limit(self._batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            published_count = 0

            for message in messages:
                try:
                    await self._broker.publish(
                        message.payload,
                        exchange=PAYMENTS_EXCHANGE,
                        routing_key=PAYMENTS_ROUTING_KEY,
                        message_id=str(message.id),
                        correlation_id=str(message.aggregate_id),
                        persist=True,
                    )
                except Exception as error:
                    message.attempts += 1
                    message.last_error = str(error)[:512]
                    logger.exception(
                        "Failed to publish outbox message",
                        outbox_id=str(message.id),
                    )
                else:
                    published_count += 1
                    message.attempts += 1
                    message.status = OutboxStatus.PROCESSED
                    message.processed_at = datetime.now(timezone.utc)
                    message.last_error = None

            await session.commit()
            return published_count

        return 0
