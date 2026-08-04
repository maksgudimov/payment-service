import asyncio
from dataclasses import dataclass
from typing import Mapping

from app.application.health.ports import HealthProbe


@dataclass(frozen=True, slots=True)
class ComponentHealth:
    status: str


@dataclass(frozen=True, slots=True)
class ServiceHealth:
    status: str
    components: dict[str, ComponentHealth]

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"


class HealthChecker:
    def __init__(
        self,
        probes: Mapping[str, HealthProbe],
        timeout_seconds: float,
    ) -> None:
        self._probes = dict(probes)
        self._timeout_seconds = timeout_seconds

    async def execute(self) -> ServiceHealth:
        names = list(self._probes)
        results = await asyncio.gather(
            *(self._check(self._probes[name]) for name in names)
        )
        components = {
            "service": ComponentHealth(status="up"),
            **dict(zip(names, results, strict=True)),
        }
        overall_status = (
            "healthy"
            if all(component.status == "up" for component in components.values())
            else "unhealthy"
        )
        return ServiceHealth(status=overall_status, components=components)

    async def _check(self, probe: HealthProbe) -> ComponentHealth:
        try:
            await asyncio.wait_for(
                probe.check(),
                timeout=self._timeout_seconds,
            )
        except Exception:
            return ComponentHealth(status="down")
        return ComponentHealth(status="up")
