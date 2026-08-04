from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.api.utils import validate_api_key
from app.api.v1.payments.handlers.post_payments import create_payment
from app.api.v1.payments.schemas.request import CreatePaymentRequestSchema
from app.application.payments import CreatePaymentResult
from app.common.enums import PaymentStatus
from app.core.config import config


class StubPaymentCreator:
    def __init__(self):
        self.command = None

    async def execute(self, command):
        self.command = command
        return CreatePaymentResult(
            payment_id=UUID("b8ed4801-e990-4be9-af28-2529f2fb3388"),
            status=PaymentStatus.PENDING,
            created_at=datetime(2026, 8, 4, 10, 0, tzinfo=timezone.utc),
        )


@pytest.mark.anyio
async def test_handler_returns_accepted_contract(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "test-api-key")
    creator = StubPaymentCreator()
    payload = CreatePaymentRequestSchema.model_validate(
        {
            "amount": "15.25",
            "currency": "EUR",
            "description": "Order 42",
            "metadata": {"order_id": 42},
            "webhook_url": "https://merchant.example/webhook",
        }
    )
    await validate_api_key("test-api-key")

    response = await create_payment(payload, "payment-42", None, creator)

    assert response.status == PaymentStatus.PENDING
    assert creator.command.idempotency_key == "payment-42"
    assert creator.command.metadata == {"order_id": 42}


@pytest.mark.anyio
async def test_rejects_invalid_api_key(monkeypatch):
    monkeypatch.setattr(config, "API_KEY", "test-api-key")

    with pytest.raises(HTTPException) as raised:
        await validate_api_key("wrong")

    assert raised.value.status_code == 401
