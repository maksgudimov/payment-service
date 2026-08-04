from decimal import Decimal

from typing import Any

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from app.common.enums import Currency


class CreatePaymentRequestSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    amount: Decimal = Field(gt=0)
    currency: Currency
    description: str = Field(
        min_length=1,
        max_length=255,
    )
    metadata: dict[str, Any] | None = None
    webhook_url: AnyHttpUrl
