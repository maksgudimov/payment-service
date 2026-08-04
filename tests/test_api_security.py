import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError

from app.api.utils import validate_idempotency_key
from app.infrastructure.cache.cache import redis


class FakeLock:
    def __init__(self, acquired=True, acquire_error=None):
        self.acquired = acquired
        self.acquire_error = acquire_error
        self.released = False

    async def acquire(self):
        if self.acquire_error is not None:
            raise self.acquire_error
        return self.acquired

    async def release(self):
        self.released = True


class FakeRedisClient:
    def __init__(self, lock):
        self._lock = lock
        self.lock_name = None

    def lock(self, name, timeout, blocking):
        self.lock_name = name
        return self._lock


@pytest.mark.anyio
async def test_acquires_and_releases_redis_lock(monkeypatch):
    lock = FakeLock()
    client = FakeRedisClient(lock)
    monkeypatch.setattr(redis, "_client", client)

    dependency = validate_idempotency_key(" payment-42 ")
    key = await anext(dependency)
    await dependency.aclose()

    assert key == "payment-42"
    assert lock.released is True
    assert "payments:idempotency:lock:" in client.lock_name
    assert "payment-42" not in client.lock_name


@pytest.mark.anyio
async def test_rejects_concurrent_request(monkeypatch):
    monkeypatch.setattr(redis, "_client", FakeRedisClient(FakeLock(False)))
    dependency = validate_idempotency_key("payment-42")

    with pytest.raises(HTTPException) as raised:
        await anext(dependency)

    assert raised.value.status_code == 409


@pytest.mark.anyio
async def test_returns_503_when_redis_is_unavailable(monkeypatch):
    client = FakeRedisClient(FakeLock(acquire_error=RedisError("down")))
    monkeypatch.setattr(redis, "_client", client)
    dependency = validate_idempotency_key("payment-42")

    with pytest.raises(HTTPException) as raised:
        await anext(dependency)

    assert raised.value.status_code == 503
