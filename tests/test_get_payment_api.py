from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import HTTPException, Response

from app.api.v1.payments.handlers.get_payments import get_payment
from app.application.payments import PaymentDetails
from app.application.payments.exceptions import PaymentNotFoundError
from app.common.enums import Currency, PaymentStatus


class StubPaymentReader:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    async def execute(self, query):
        if self.error is not None:
            raise self.error
        return self.result


@pytest.mark.anyio
async def test_returns_details_and_disables_http_caching():
    payment_id = uuid4()
    details = PaymentDetails(
        payment_id=payment_id,
        amount=Decimal("10.25"),
        currency=Currency.EUR,
        description="Invoice",
        metadata={"invoice_id": 7},
        status=PaymentStatus.PENDING,
        webhook_url="https://merchant.example/webhook",
        created_at=datetime.now(timezone.utc),
        processed_at=None,
        webhook_delivered_at=None,
    )
    response = Response()

    result = await get_payment(
        payment_id, response, None, StubPaymentReader(result=details)
    )

    assert result.payment_id == payment_id
    assert result.status == PaymentStatus.PENDING
    assert result.metadata == {"invoice_id": 7}
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"


@pytest.mark.anyio
async def test_maps_missing_payment_to_404():
    with pytest.raises(HTTPException) as raised:
        await get_payment(
            uuid4(),
            Response(),
            None,
            StubPaymentReader(error=PaymentNotFoundError()),
        )

    assert raised.value.status_code == 404
    assert raised.value.detail == "Payment not found"
