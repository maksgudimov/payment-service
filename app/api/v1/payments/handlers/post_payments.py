from typing import Annotated

from fastapi import Depends

from app.api.dependencies import get_payment_creator
from app.api.utils import validate_api_key, validate_idempotency_key
from app.api.v1.payments.schemas.request import CreatePaymentRequestSchema
from app.api.v1.payments.schemas.response import CreatePaymentAcceptedResponseSchema
from app.application.payments import CreatePaymentCommand, PaymentCreator


async def create_payment(
    payload: CreatePaymentRequestSchema,
    idempotency_key: Annotated[str, Depends(validate_idempotency_key)],
    _: Annotated[None, Depends(validate_api_key)],
    creator: Annotated[PaymentCreator, Depends(get_payment_creator)],
) -> CreatePaymentAcceptedResponseSchema:
    result = await creator.execute(
        CreatePaymentCommand(
            amount=payload.amount,
            currency=payload.currency,
            description=payload.description,
            metadata=payload.metadata,
            webhook_url=str(payload.webhook_url),
            idempotency_key=idempotency_key,
        )
    )
    return CreatePaymentAcceptedResponseSchema(
        payment_id=result.payment_id,
        status=result.status,
        created_at=result.created_at,
    )
