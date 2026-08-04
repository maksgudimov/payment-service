from collections.abc import AsyncGenerator
from hashlib import sha256
from hmac import compare_digest
from typing import Annotated

import structlog
from fastapi import Header, HTTPException, status
from redis.exceptions import LockError, RedisError

from app.core.config import config
from app.infrastructure.cache.cache import redis


logger = structlog.get_logger(__name__)


async def validate_api_key(
    api_key: Annotated[
        str,
        Header(alias="X-API-Key", min_length=1, max_length=255),
    ],
) -> None:
    if not config.API_KEY:
        logger.error("API_KEY is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API authentication is not configured",
        )

    if not compare_digest(api_key, config.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )


async def validate_idempotency_key(
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=255),
    ],
) -> AsyncGenerator[str, None]:
    normalized_key = idempotency_key.strip()
    if not normalized_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key is required",
        )

    key_digest = sha256(normalized_key.encode("utf-8")).hexdigest()
    lock = redis.client.lock(
        name=f"payments:idempotency:lock:{key_digest}",
        timeout=config.IDEMPOTENCY_LOCK_TTL_SECONDS,
        blocking=False,
    )

    try:
        acquired = await lock.acquire()
    except RedisError as error:
        logger.exception("Failed to acquire idempotency lock")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Idempotency service is unavailable",
        ) from error

    if not acquired:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A request with this Idempotency-Key is already being processed",
        )

    try:
        yield normalized_key
    finally:
        try:
            await lock.release()
        except LockError:
            logger.warning("Idempotency lock expired before release")
        except RedisError:
            logger.exception("Failed to release idempotency lock")
