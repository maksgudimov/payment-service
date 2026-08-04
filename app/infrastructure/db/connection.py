import structlog
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Config
from app.infrastructure.base import BaseConnection


logger = structlog.get_logger(__name__)


class PostgresConnectionClient(BaseConnection):
    def __init__(self, config: Config):
        self._config = config
        self._driver = "asyncpg"

        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def url(self) -> str:
        return (
            f"postgresql+{self._driver}://"
            f"{self._config.POSTGRES_USER}:"
            f"{self._config.POSTGRES_PASSWORD}@"
            f"{self._config.POSTGRES_HOST}:"
            f"{self._config.POSTGRES_PORT}/"
            f"{self._config.POSTGRES_DB}"
        )

    def connect(self) -> None:
        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self.url,
            echo=False,
            pool_pre_ping=True,
            pool_size=self._config.DB_POOL_SIZE,
            max_overflow=self._config.DB_MAX_OVERFLOW,
        )

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("Database is not initialized. Call connect().")

        return self._engine

    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        if self._session_factory is None:
            raise RuntimeError("Database is not initialized. Call connect().")

        async with self._session_factory() as session:
            yield session

    async def ping(self) -> None:
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            logger.info("Database connection established.")

        except SQLAlchemyError as e:
            logger.exception("Failed to connect to Database.")
            raise RuntimeError("Database is unavailable.") from e

    async def disconnect(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
