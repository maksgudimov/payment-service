from faststream.rabbit import RabbitBroker
from sqlalchemy import text

from app.infrastructure.cache.connection import RedisConnectionClient
from app.infrastructure.db.connection import PostgresConnectionClient


class PostgresHealthProbe:
    def __init__(self, database: PostgresConnectionClient) -> None:
        self._database = database

    async def check(self) -> None:
        async with self._database.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))


class RedisHealthProbe:
    def __init__(self, redis: RedisConnectionClient) -> None:
        self._redis = redis

    async def check(self) -> None:
        if not await self._redis.client.ping():
            raise RuntimeError("Redis ping failed")


class RabbitHealthProbe:
    def __init__(self, broker: RabbitBroker, timeout_seconds: float) -> None:
        self._broker = broker
        self._timeout_seconds = timeout_seconds

    async def check(self) -> None:
        if not await self._broker.ping(timeout=self._timeout_seconds):
            raise RuntimeError("RabbitMQ ping failed")
