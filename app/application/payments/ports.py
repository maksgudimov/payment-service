from types import TracebackType
from datetime import datetime
from typing import Protocol, Self
from uuid import UUID

from app.common.enums import PaymentStatus
from app.domain.payments.entities import Payment
from app.domain.payments.events import PaymentCreated


class DuplicateIdempotencyKeyError(Exception):
    pass


class PaymentRepository(Protocol):
    async def get_by_idempotency_key(self, key: str) -> Payment | None: ...
    async def get_by_id(self, payment_id: UUID, *, for_update: bool = False) -> Payment | None: ...
    async def add(self, payment: Payment) -> None: ...
    async def mark_processed(
        self,
        payment_id: UUID,
        status: "PaymentStatus",
        processed_at: datetime,
    ) -> None: ...
    async def mark_webhook_delivered(
        self,
        payment_id: UUID,
        delivered_at: datetime,
    ) -> None: ...


class OutboxRepository(Protocol):
    async def add(self, event: PaymentCreated) -> None: ...


class PaymentUnitOfWork(Protocol):
    payments: PaymentRepository
    outbox: OutboxRepository

    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    async def commit(self) -> None: ...


class PaymentGateway(Protocol):
    async def process(self, payment: Payment) -> "PaymentStatus": ...


class WebhookClient(Protocol):
    async def send_payment_result(self, payment: Payment) -> None: ...
