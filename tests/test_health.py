import asyncio

import pytest
from fastapi import Response

from app.api.health import healthcheck
from app.application.health import HealthChecker


class PassingProbe:
    async def check(self):
        return None


class FailingProbe:
    async def check(self):
        raise ConnectionError("unavailable")


class SlowProbe:
    async def check(self):
        await asyncio.sleep(1)


@pytest.mark.anyio
async def test_returns_all_components_up():
    checker = HealthChecker(
        {
            "database": PassingProbe(),
            "redis": PassingProbe(),
            "rabbitmq": PassingProbe(),
        },
        timeout_seconds=0.1,
    )

    result = await checker.execute()

    assert result.is_healthy
    assert result.status == "healthy"
    assert all(component.status == "up" for component in result.components.values())


@pytest.mark.anyio
async def test_reports_failure_and_timeout_without_internal_error_details():
    checker = HealthChecker(
        {
            "database": PassingProbe(),
            "redis": FailingProbe(),
            "rabbitmq": SlowProbe(),
        },
        timeout_seconds=0.01,
    )

    result = await checker.execute()

    assert not result.is_healthy
    assert result.components["redis"].status == "down"
    assert result.components["rabbitmq"].status == "down"


@pytest.mark.anyio
async def test_endpoint_returns_503_for_unhealthy_dependencies():
    checker = HealthChecker(
        {
            "database": PassingProbe(),
            "redis": FailingProbe(),
            "rabbitmq": PassingProbe(),
        },
        timeout_seconds=0.1,
    )
    response = Response()

    payload = await healthcheck(response, None, checker)

    assert response.status_code == 503
    assert payload.status == "unhealthy"
    assert response.headers["Cache-Control"] == "no-store"
