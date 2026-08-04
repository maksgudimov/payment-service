from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.common.enums import Currency, PaymentStatus
from app.core.config import Config
from app.domain.payments.entities import Payment
from app.infrastructure.http.webhook import AioHttpWebhookClient


class FakeResponse:
    def __init__(self, status):
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    async def text(self):
        return "temporary failure"


class FakeSession:
    def __init__(self, statuses):
        self.closed = False
        self._statuses = iter(statuses)
        self.requests = []

    def post(self, url, *, json, headers):
        self.requests.append((url, json, headers))
        return FakeResponse(next(self._statuses))


@pytest.mark.anyio
async def test_retries_three_times_with_exponential_delay():
    config = Config()
    config.WEBHOOK_RETRY_ATTEMPTS = 3
    config.WEBHOOK_RETRY_BASE_DELAY_SECONDS = 1
    delays = []

    async def record_sleep(delay):
        delays.append(delay)

    client = AioHttpWebhookClient(config, sleep=record_sleep)
    session = FakeSession([500, 502, 204])
    client._session = session
    payment = Payment(
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        description="Order",
        metadata=None,
        idempotency_key="order-1",
        webhook_url="https://merchant.example/webhook",
        status=PaymentStatus.SUCCEEDED,
        processed_at=datetime.now(timezone.utc),
    )

    await client.send_payment_result(payment)

    assert len(session.requests) == 3
    assert delays == [1, 2]
    assert session.requests[0][2]["Idempotency-Key"] == (
        f"payment-result:{payment.id}"
    )
