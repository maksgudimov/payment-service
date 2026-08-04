from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from app.application.payments.ports import (
    PaymentGateway,
    PaymentUnitOfWork,
    WebhookClient,
)
from app.application.payments.exceptions import PaymentNotFoundError
from app.common.enums import PaymentStatus
from app.domain.payments.entities import Payment


class PaymentProcessor:

    def __init__(
        self,
        uow_factory: Callable[[], PaymentUnitOfWork],
        gateway: PaymentGateway,
        webhook_client: WebhookClient,
    ) -> None:
        self._uow_factory = uow_factory
        self._gateway = gateway
        self._webhook_client = webhook_client

    async def execute(self, payment_id: UUID) -> None:
        payment = await self._load(payment_id)
        if payment.webhook_delivered_at is not None:
            return

        if payment.status is PaymentStatus.PENDING:
            result_status = await self._gateway.process(payment)
            processed_at = datetime.now(timezone.utc)
            async with self._uow_factory() as uow:
                current = await uow.payments.get_by_id(payment_id, for_update=True)
                if current is None:
                    raise PaymentNotFoundError(str(payment_id))
                if current.status is PaymentStatus.PENDING:
                    await uow.payments.mark_processed(
                        payment_id,
                        result_status,
                        processed_at,
                    )
                    await uow.commit()
                    payment = self._processed_copy(
                        current,
                        result_status,
                        processed_at,
                    )
                else:
                    payment = current

        await self._webhook_client.send_payment_result(payment)

        async with self._uow_factory() as uow:
            current = await uow.payments.get_by_id(payment_id, for_update=True)
            if current is None:
                raise PaymentNotFoundError(str(payment_id))
            if current.webhook_delivered_at is None:
                await uow.payments.mark_webhook_delivered(
                    payment_id,
                    datetime.now(timezone.utc),
                )
                await uow.commit()

    async def _load(self, payment_id: UUID) -> Payment:
        async with self._uow_factory() as uow:
            payment = await uow.payments.get_by_id(payment_id)
            if payment is None:
                raise PaymentNotFoundError(str(payment_id))
            return payment

    @staticmethod
    def _processed_copy(
        payment: Payment,
        status: PaymentStatus,
        processed_at: datetime,
    ) -> Payment:
        return Payment(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.metadata,
            status=status,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=processed_at,
            webhook_delivered_at=payment.webhook_delivered_at,
        )
