from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Response, status

from app.api.dependencies import get_payment_reader
from app.api.utils import validate_api_key
from app.api.v1.payments.schemas.response import PaymentResponseSchema
from app.application.payments import GetPaymentQuery, PaymentReader
from app.application.payments.exceptions import PaymentNotFoundError


async def get_payment(
    payment_id: UUID,
    response: Response,
    _: Annotated[None, Depends(validate_api_key)],
    reader: Annotated[PaymentReader, Depends(get_payment_reader)],
) -> PaymentResponseSchema:
    try:
        payment = await reader.execute(GetPaymentQuery(payment_id=payment_id))
    except PaymentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        ) from error

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return PaymentResponseSchema(
        payment_id=payment.payment_id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        metadata=payment.metadata,
        status=payment.status,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
        webhook_delivered_at=payment.webhook_delivered_at,
    )
