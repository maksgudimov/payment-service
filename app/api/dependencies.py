from collections.abc import AsyncGenerator
from functools import partial
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.payments import PaymentCreator, PaymentReader
from app.application.health import HealthChecker
from app.core.config import config
from app.infrastructure.broker.broker import rabbitmq
from app.infrastructure.cache.cache import redis
from app.infrastructure.db.database import database
from app.infrastructure.health import (
    PostgresHealthProbe,
    RabbitHealthProbe,
    RedisHealthProbe,
)
from app.infrastructure.uow import SQLAlchemyPaymentUnitOfWork


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in database.session():
        yield session


def get_payment_creator(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PaymentCreator:
    return PaymentCreator(partial(SQLAlchemyPaymentUnitOfWork, session))


def get_payment_reader(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PaymentReader:
    return PaymentReader(partial(SQLAlchemyPaymentUnitOfWork, session))


def get_health_checker() -> HealthChecker:
    return HealthChecker(
        probes={
            "database": PostgresHealthProbe(database),
            "redis": RedisHealthProbe(redis),
            "rabbitmq": RabbitHealthProbe(
                rabbitmq,
                config.HEALTHCHECK_TIMEOUT_SECONDS,
            ),
        },
        timeout_seconds=config.HEALTHCHECK_TIMEOUT_SECONDS,
    )
