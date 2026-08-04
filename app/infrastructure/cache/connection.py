import structlog
from redis.asyncio import Redis

from app.core.config import Config
from app.infrastructure.base import BaseConnection

logger = structlog.get_logger(__name__)


class RedisConnectionClient(BaseConnection):
    def __init__(self, config: Config) -> None:
        self._config: Config = config
        self._client: Redis | None = None

    @property
    def url(self) -> str:
        return (
            f"redis://{self._config.REDIS_HOST}:"
            f"{self._config.REDIS_PORT}/"
            f"{self._config.REDIS_DB}"
        )

    async def start(self) -> None:
        self._client = Redis(
            host=self._config.REDIS_HOST,
            port=self._config.REDIS_PORT,
            db=self._config.REDIS_DB,
            decode_responses=True,
        )

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def ping(self) -> None:
        if self._client is None:
            raise RuntimeError("Redis client is not started")

        try:
            await self._client.ping()
            logger.info("Redis connection established.")
        except Exception:
            logger.exception("Failed to connect to Redis.")
            raise

    @property
    def client(self) -> Redis:
        if self._client is None:
            raise RuntimeError("Redis client is not started")

        return self._client
