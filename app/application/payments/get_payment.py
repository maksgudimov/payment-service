from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from app.application.payments.exceptions import PaymentNotFoundError
from app.application.payments.ports import PaymentUnitOfWork
from app.common.enums import Currency, PaymentStatus
from app.domain.payments.entities import Payment


@dataclass(frozen=True, slots=True)
class GetPaymentQuery:
    payment_id: UUID


@dataclass(frozen=True, slots=True)
class PaymentDetails:
    payment_id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] | None
    status: PaymentStatus
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None
    webhook_delivered_at: datetime | None

    @classmethod
    def from_payment(cls, payment: Payment) -> "PaymentDetails":
        return cls(
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.metadata,
            status=payment.status,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
            webhook_delivered_at=payment.webhook_delivered_at,
        )


class PaymentReader:
    def __init__(self, uow_factory: Callable[[], PaymentUnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def execute(self, query: GetPaymentQuery) -> PaymentDetails:
        async with self._uow_factory() as uow:
            payment = await uow.payments.get_by_id(query.payment_id)
            if payment is None:
                raise PaymentNotFoundError(str(query.payment_id))
            return PaymentDetails.from_payment(payment)
