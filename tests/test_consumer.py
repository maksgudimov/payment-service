from datetime import datetime, timezone
from uuid import uuid4

import pytest
from faststream.exceptions import RejectMessage

import app.consumer as consumer_module
from app.messaging.schemas import PaymentCreatedMessage


@pytest.mark.anyio
async def test_consumer_rejects_failed_message_with_requeue(monkeypatch):
    event = PaymentCreatedMessage(
        event_id=uuid4(),
        event_type="payment.created",
        payment_id=uuid4(),
        occurred_at=datetime.now(timezone.utc),
    )

    async def fail_processing(received_event):
        raise RuntimeError("webhook failed")

    monkeypatch.setattr(
        consumer_module,
        "process_payment_created",
        fail_processing,
    )

    with pytest.raises(RejectMessage) as raised:
        await consumer_module.consume_payment_created._original_call(event)

    assert raised.value.extra_options == {"requeue": True}
