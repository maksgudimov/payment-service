from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import EventType, OutboxStatus
from app.domain.payments.events import PaymentCreated
from app.models.outbox import OutboxMessage


class SQLAlchemyOutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: PaymentCreated) -> None:
        self._session.add(
            OutboxMessage(
                id=event.event_id,
                aggregate_id=event.payment_id,
                event_type=EventType.PAYMENT_CREATED,
                payload=event.as_payload(),
                status=OutboxStatus.PENDING,
                attempts=0,
                created_at=event.occurred_at,
            )
        )
