from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class PaymentCreated:
    payment_id: UUID
    occurred_at: datetime
    event_id: UUID = field(default_factory=uuid4)
    event_type: str = "payment.created"

    @classmethod
    def from_payment(cls, payment_id: UUID, created_at: datetime) -> "PaymentCreated":
        return cls(payment_id=payment_id, occurred_at=created_at)

    def as_payload(self) -> dict[str, str]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "payment_id": str(self.payment_id),
            "occurred_at": self.occurred_at.isoformat(),
        }
