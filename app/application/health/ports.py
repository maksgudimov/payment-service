from typing import Protocol


class HealthProbe(Protocol):
    async def check(self) -> None: ...
