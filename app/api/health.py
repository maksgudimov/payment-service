from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from app.api.dependencies import get_health_checker
from app.api.utils import validate_api_key
from app.application.health import HealthChecker


class ComponentHealthSchema(BaseModel):
    status: Literal["up", "down"]


class HealthResponseSchema(BaseModel):
    status: Literal["healthy", "unhealthy"]
    components: dict[str, ComponentHealthSchema]


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponseSchema,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid API key"},
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "One or more dependencies are unavailable"
        },
    },
)
async def healthcheck(
    response: Response,
    _: Annotated[None, Depends(validate_api_key)],
    checker: Annotated[HealthChecker, Depends(get_health_checker)],
) -> HealthResponseSchema:
    result = await checker.execute()
    if not result.is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    response.headers["Cache-Control"] = "no-store"

    return HealthResponseSchema(
        status=result.status,
        components={
            name: ComponentHealthSchema(status=component.status)
            for name, component in result.components.items()
        },
    )
