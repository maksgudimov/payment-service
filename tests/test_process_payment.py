from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.application.payments import PaymentProcessor
from app.common.enums import Currency, PaymentStatus
from app.domain.payments.entities import Payment


class ProcessingPaymentRepository:
    def __init__(self, payment):
        self.payment = payment

    async def get_by_id(self, payment_id, *, for_update=False):
        return self.payment if self.payment.id == payment_id else None

    async def mark_processed(self, payment_id, status, processed_at):
        self.payment = replace(
            self.payment, status=status, processed_at=processed_at
        )

    async def mark_webhook_delivered(self, payment_id, delivered_at):
        self.payment = replace(self.payment, webhook_delivered_at=delivered_at)


class ProcessingUnitOfWork:
    def __init__(self, repository):
        self.payments = repository
        self.outbox = None
        self.commits = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def commit(self):
        self.commits += 1


class SuccessfulGateway:
    def __init__(self):
        self.calls = 0

    async def process(self, payment):
        self.calls += 1
        return PaymentStatus.SUCCEEDED


class RecordingWebhookClient:
    def __init__(self):
        self.payments = []

    async def send_payment_result(self, payment):
        self.payments.append(payment)


@pytest.fixture
def processing_context():
    payment = Payment(
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        description="Order",
        metadata=None,
        idempotency_key="order-1",
        webhook_url="https://merchant.example/webhook",
    )
    repository = ProcessingPaymentRepository(payment)
    uow = ProcessingUnitOfWork(repository)
    gateway = SuccessfulGateway()
    webhook = RecordingWebhookClient()
    processor = PaymentProcessor(lambda: uow, gateway, webhook)
    return payment, repository, uow, gateway, webhook, processor


@pytest.mark.anyio
async def test_processes_payment_and_marks_webhook_delivered(processing_context):
    payment, repository, uow, gateway, webhook, processor = processing_context

    await processor.execute(payment.id)

    assert repository.payment.status == PaymentStatus.SUCCEEDED
    assert repository.payment.processed_at is not None
    assert repository.payment.webhook_delivered_at is not None
    assert gateway.calls == 1
    assert len(webhook.payments) == 1
    assert uow.commits == 2


@pytest.mark.anyio
async def test_redelivery_after_webhook_delivery_is_noop(processing_context):
    payment, repository, _, gateway, webhook, processor = processing_context
    repository.payment = replace(
        payment,
        status=PaymentStatus.SUCCEEDED,
        processed_at=datetime.now(timezone.utc),
        webhook_delivered_at=datetime.now(timezone.utc),
    )

    await processor.execute(payment.id)

    assert gateway.calls == 0
    assert webhook.payments == []
