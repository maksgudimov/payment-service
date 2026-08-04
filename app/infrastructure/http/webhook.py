import asyncio
from collections.abc import Awaitable, Callable

import aiohttp
import structlog

from app.core.config import Config
from app.domain.payments.entities import Payment


logger = structlog.get_logger(__name__)


class WebhookDeliveryError(Exception):
    pass


class AioHttpWebhookClient:
    def __init__(
        self,
        config: Config,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._timeout = aiohttp.ClientTimeout(total=config.WEBHOOK_TIMEOUT_SECONDS)
        self._attempts = config.WEBHOOK_RETRY_ATTEMPTS
        self._base_delay = config.WEBHOOK_RETRY_BASE_DELAY_SECONDS
        self._sleep = sleep
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def send_payment_result(self, payment: Payment) -> None:
        if self._session is None or self._session.closed:
            raise RuntimeError("Webhook client is not started")

        payload = {
            "payment_id": str(payment.id),
            "status": payment.status.value,
            "processed_at": (
                payment.processed_at.isoformat() if payment.processed_at else None
            ),
        }
        headers = {
            "Idempotency-Key": f"payment-result:{payment.id}",
            "Content-Type": "application/json",
        }

        last_error: BaseException | None = None
        for attempt in range(1, self._attempts + 1):
            try:
                async with self._session.post(
                    payment.webhook_url,
                    json=payload,
                    headers=headers,
                ) as response:
                    if 200 <= response.status < 300:
                        return
                    body = (await response.text())[:512]
                    raise WebhookDeliveryError(
                        f"Webhook returned HTTP {response.status}: {body}"
                    )
            except (aiohttp.ClientError, asyncio.TimeoutError, WebhookDeliveryError) as error:
                last_error = error
                logger.warning(
                    "Webhook delivery attempt failed",
                    payment_id=str(payment.id),
                    attempt=attempt,
                    max_attempts=self._attempts,
                    error=str(error),
                )
                if attempt < self._attempts:
                    await self._sleep(self._base_delay * (2 ** (attempt - 1)))

        raise WebhookDeliveryError(
            f"Webhook delivery failed after {self._attempts} attempts"
        ) from last_error
