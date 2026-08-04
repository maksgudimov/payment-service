from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.common.enums import Currency, PaymentStatus


class CreatePaymentAcceptedResponseSchema(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class PaymentResponseSchema(CreatePaymentAcceptedResponseSchema):
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] | None
    webhook_url: str
    processed_at: datetime | None
    webhook_delivered_at: datetime | None
