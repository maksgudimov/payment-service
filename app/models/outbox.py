from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    String,
    DateTime,
    JSON,
    Enum,
    Integer,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.common.enums import OutboxStatus, EventType
from app.models.base import Base


class OutboxMessage(Base):
    __tablename__ = "outbox"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Уникальный идентификатор сообщения",
    )
    aggregate_id = Column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="ID связанной сущности (payment_id)",
    )
    event_type = Column(
        Enum(EventType, name="event_type_enum"),
        nullable=False,
        doc="Тип события (payment.created, payment.processed)",
    )
    payload = Column(
        JSON,
        nullable=False,
        doc="Данные события в формате JSON",
    )
    status = Column(
        Enum(OutboxStatus, name="outbox_status"),
        nullable=False,
        default=OutboxStatus.PENDING.value,
        doc="Статус обработки",
    )
    attempts = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Количество попыток отправки",
    )
    last_error = Column(
        String(512),
        nullable=True,
        doc="Последняя ошибка",
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
        doc="Дата успешной обработки",
    )

    __table_args__ = (
        Index("idx_outbox_status_created", "status", "created_at"),
        Index("idx_outbox_aggregate_id", "aggregate_id"),
    )

    def __repr__(self):
        return f"<OutboxMessage(id={self.id}, event_type={self.event_type}, status={self.status})>"
