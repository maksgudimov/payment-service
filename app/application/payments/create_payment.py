from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from app.application.payments.ports import (
    DuplicateIdempotencyKeyError,
    PaymentUnitOfWork,
)
from app.common.enums import Currency, PaymentStatus
from app.domain.payments.entities import Payment
from app.domain.payments.events import PaymentCreated


@dataclass(frozen=True, slots=True)
class CreatePaymentCommand:
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] | None
    webhook_url: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class CreatePaymentResult:
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime

    @classmethod
    def from_payment(cls, payment: Payment) -> "CreatePaymentResult":
        return cls(
            payment_id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
        )


class PaymentCreator:
    def __init__(self, uow_factory: Callable[[], PaymentUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def execute(self, command: CreatePaymentCommand) -> CreatePaymentResult:
        payment = Payment(
            amount=command.amount,
            currency=command.currency,
            description=command.description,
            metadata=command.metadata,
            webhook_url=command.webhook_url,
            idempotency_key=command.idempotency_key,
        )

        try:
            async with self._uow_factory() as uow:
                existing = await uow.payments.get_by_idempotency_key(
                    command.idempotency_key
                )
                if existing is not None:
                    return CreatePaymentResult.from_payment(existing)

                await uow.payments.add(payment)
                await uow.outbox.add(
                    PaymentCreated.from_payment(payment.id, payment.created_at)
                )
                await uow.commit()
        except DuplicateIdempotencyKeyError:
            async with self._uow_factory() as uow:
                existing = await uow.payments.get_by_idempotency_key(
                    command.idempotency_key
                )
                if existing is None:
                    raise
                return CreatePaymentResult.from_payment(existing)

        return CreatePaymentResult.from_payment(payment)
