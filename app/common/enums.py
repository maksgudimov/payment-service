from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value


class OutboxStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

    def __str__(self) -> str:
        return self.value


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"

    def __str__(self) -> str:
        return self.value


class EventType(str, Enum):
    PAYMENT_CREATED = "payment.created"
    PAYMENT_PROCESSED = "payment.processed"

    def __str__(self) -> str:
        return self.value
