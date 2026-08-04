from decimal import Decimal

import pytest

from app.application.payments import CreatePaymentCommand, PaymentCreator
from app.application.payments.ports import DuplicateIdempotencyKeyError
from app.common.enums import Currency, PaymentStatus


class FakePaymentRepository:
    def __init__(self):
        self.items = {}

    async def get_by_idempotency_key(self, key):
        return self.items.get(key)

    async def add(self, payment):
        self.items[payment.idempotency_key] = payment


class FakeOutboxRepository:
    def __init__(self):
        self.events = []

    async def add(self, event):
        self.events.append(event)


class FakeUnitOfWork:
    def __init__(self, payments, outbox):
        self.payments = payments
        self.outbox = outbox
        self.commits = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def commit(self):
        self.commits += 1


class ConflictingUnitOfWork(FakeUnitOfWork):
    async def commit(self):
        raise DuplicateIdempotencyKeyError


@pytest.fixture
def payment_context():
    payments = FakePaymentRepository()
    outbox = FakeOutboxRepository()
    uow = FakeUnitOfWork(payments, outbox)
    creator = PaymentCreator(lambda: uow)
    command = CreatePaymentCommand(
        amount=Decimal("1250.50"),
        currency=Currency.RUB,
        description="Order 42",
        metadata={"order_id": 42},
        webhook_url="https://merchant.example/webhooks/payments",
        idempotency_key="order-42-attempt-1",
    )
    return payments, outbox, uow, creator, command


@pytest.mark.anyio
async def test_creates_pending_payment_and_outbox_event(payment_context):
    _, outbox, uow, creator, command = payment_context
    result = await creator.execute(command)

    assert result.status == PaymentStatus.PENDING
    assert uow.commits == 1
    assert len(outbox.events) == 1
    assert outbox.events[0].payment_id == result.payment_id
    assert outbox.events[0].event_type == "payment.created"


@pytest.mark.anyio
async def test_same_idempotency_key_returns_original_payment(payment_context):
    _, outbox, uow, creator, command = payment_context
    first = await creator.execute(command)
    second = await creator.execute(command)

    assert second == first
    assert uow.commits == 1
    assert len(outbox.events) == 1


@pytest.mark.anyio
async def test_concurrent_duplicate_returns_winning_payment(payment_context):
    payments, outbox, _, _, command = payment_context
    creator = PaymentCreator(lambda: ConflictingUnitOfWork(payments, outbox))

    result = await creator.execute(command)
    winner = await payments.get_by_idempotency_key(command.idempotency_key)

    assert result.payment_id == winner.id
