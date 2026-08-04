from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Numeric,
    Enum,
    JSON,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.common.enums import PaymentStatus, Currency
from app.models.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Уникальный идентификатор платежа",
    )
    amount = Column(
        Numeric(10, 2),
        nullable=False,
        doc="Сумма платежа",
    )
    currency = Column(
        Enum(Currency, name="currency_enum"),
        nullable=False,
        doc="Валюта (RUB, USD, EUR)",
    )
    description = Column(
        String(255),
        nullable=False,
        doc="Описание платежа",
    )
    payload_meta = Column(
        JSON,
        nullable=True,
        doc="Метаданные в формате JSON",
    )
    status = Column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING.value,
        doc="Статус платежа",
    )
    idempotency_key = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        doc="Ключ идемпотентности",
    )
    webhook_url = Column(
        String(512),
        nullable=False,
        doc="URL для webhook уведомлений",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        doc="Дата создания",
    )
    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Дата обработки",
    )
    webhook_delivered_at = Column(
        DateTime(timezone=True),
        nullable=True,
        doc="Date when the result webhook was delivered successfully",
    )

    __table_args__ = (
        Index("idx_payments_status_created", "status", "created_at"),
        Index("idx_payments_idempotency_key", "idempotency_key"),
    )

    def __repr__(self):
        return f"<Payment(id={self.id}, status={self.status}, amount={self.amount} {self.currency})>"
