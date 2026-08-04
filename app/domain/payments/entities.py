from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.common.enums import Currency, PaymentStatus


@dataclass(frozen=True, slots=True)
class Payment:
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] | None
    idempotency_key: str
    webhook_url: str
    id: UUID = field(default_factory=uuid4)
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    processed_at: datetime | None = None
    webhook_delivered_at: datetime | None = None
