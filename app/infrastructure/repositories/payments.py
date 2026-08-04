from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.payments.entities import Payment
from app.common.enums import PaymentStatus
from app.models.payment import Payment as PaymentModel


class SQLAlchemyPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        model = await self._session.scalar(
            select(PaymentModel).where(PaymentModel.idempotency_key == key)
        )
        return self._to_domain(model) if model is not None else None

    async def add(self, payment: Payment) -> None:
        self._session.add(
            PaymentModel(
                id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
                description=payment.description,
                payload_meta=payment.metadata,
                status=payment.status,
                idempotency_key=payment.idempotency_key,
                webhook_url=payment.webhook_url,
                created_at=payment.created_at,
                processed_at=payment.processed_at,
            )
        )

    async def get_by_id(
        self,
        payment_id: UUID,
        *,
        for_update: bool = False,
    ) -> Payment | None:
        query = select(PaymentModel).where(PaymentModel.id == payment_id)
        if for_update:
            query = query.with_for_update()
        model = await self._session.scalar(query)
        return self._to_domain(model) if model is not None else None

    async def mark_processed(
        self,
        payment_id: UUID,
        status: PaymentStatus,
        processed_at: datetime,
    ) -> None:
        await self._session.execute(
            update(PaymentModel)
            .where(PaymentModel.id == payment_id)
            .values(status=status, processed_at=processed_at)
        )

    async def mark_webhook_delivered(
        self,
        payment_id: UUID,
        delivered_at: datetime,
    ) -> None:
        await self._session.execute(
            update(PaymentModel)
            .where(PaymentModel.id == payment_id)
            .values(webhook_delivered_at=delivered_at)
        )

    @staticmethod
    def _to_domain(model: PaymentModel) -> Payment:
        return Payment(
            id=model.id,
            amount=model.amount,
            currency=model.currency,
            description=model.description,
            metadata=model.payload_meta,
            status=model.status,
            idempotency_key=model.idempotency_key,
            webhook_url=model.webhook_url,
            created_at=model.created_at,
            processed_at=model.processed_at,
            webhook_delivered_at=model.webhook_delivered_at,
        )
