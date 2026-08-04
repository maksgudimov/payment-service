import asyncio
import random
from collections.abc import Awaitable, Callable

from app.common.enums import PaymentStatus
from app.core.config import Config
from app.domain.payments.entities import Payment


class SimulatedPaymentGateway:
    def __init__(
        self,
        config: Config,
        *,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        random_value: Callable[[], float] = random.random,
        random_delay: Callable[[float, float], float] = random.uniform,
    ) -> None:
        self._min_delay = config.PAYMENT_PROCESSING_MIN_SECONDS
        self._max_delay = config.PAYMENT_PROCESSING_MAX_SECONDS
        self._sleep = sleep
        self._random_value = random_value
        self._random_delay = random_delay

    async def process(self, payment: Payment) -> PaymentStatus:
        await self._sleep(self._random_delay(self._min_delay, self._max_delay))
        return (
            PaymentStatus.SUCCEEDED
            if self._random_value() < 0.9
            else PaymentStatus.FAILED
        )
