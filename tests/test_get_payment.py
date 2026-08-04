from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.payments import GetPaymentQuery, PaymentReader
from app.application.payments.exceptions import PaymentNotFoundError
from app.common.enums import Currency, PaymentStatus
from app.domain.payments.entities import Payment


class ReadPaymentRepository:
    def __init__(self, payment=None):
        self.payment = payment

    async def get_by_id(self, payment_id, *, for_update=False):
        if self.payment is not None and self.payment.id == payment_id:
            return self.payment
        return None


class ReadUnitOfWork:
    def __init__(self, repository):
        self.payments = repository
        self.outbox = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def commit(self):
        raise AssertionError("Read use case must not commit")


@pytest.mark.anyio
async def test_returns_authoritative_payment_details():
    processed_at = datetime.now(timezone.utc)
    payment = Payment(
        amount=Decimal("2500.50"),
        currency=Currency.USD,
        description="Invoice 100",
        metadata={"invoice_id": 100},
        idempotency_key="invoice-100",
        webhook_url="https://merchant.example/webhook",
        status=PaymentStatus.SUCCEEDED,
        processed_at=processed_at,
    )
    reader = PaymentReader(lambda: ReadUnitOfWork(ReadPaymentRepository(payment)))

    result = await reader.execute(GetPaymentQuery(payment.id))

    assert result.payment_id == payment.id
    assert result.amount == Decimal("2500.50")
    assert result.status == PaymentStatus.SUCCEEDED
    assert result.metadata == {"invoice_id": 100}
    assert result.processed_at == processed_at


@pytest.mark.anyio
async def test_raises_not_found_for_unknown_payment():
    reader = PaymentReader(lambda: ReadUnitOfWork(ReadPaymentRepository()))

    with pytest.raises(PaymentNotFoundError):
        await reader.execute(GetPaymentQuery(uuid4()))
