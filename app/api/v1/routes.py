from fastapi import APIRouter
from starlette import status as http_status

from app.api.v1.payments.schemas.response import (
    CreatePaymentAcceptedResponseSchema,
    PaymentResponseSchema,
)
from app.api.v1 import payments


payments_router = APIRouter(prefix="/payments", tags=["Payments"])


payments_router.add_api_route(
    path="",
    endpoint=payments.create_payment,
    methods=["POST"],
    status_code=http_status.HTTP_202_ACCEPTED,
    response_model=CreatePaymentAcceptedResponseSchema,
)


payments_router.add_api_route(
    path="/{payment_id}",
    endpoint=payments.get_payment,
    methods=["GET"],
    status_code=http_status.HTTP_200_OK,
    response_model=PaymentResponseSchema,
    responses={
        http_status.HTTP_401_UNAUTHORIZED: {"description": "Invalid API key"},
        http_status.HTTP_404_NOT_FOUND: {"description": "Payment not found"},
    },
)
