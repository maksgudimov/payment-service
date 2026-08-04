import structlog
from fastapi import FastAPI
from contextlib import asynccontextmanager

from starlette.middleware.cors import CORSMiddleware

from app.api.v1 import payments_router
from app.api.health import router as health_router
from app.core.config import config
from app.infrastructure.broker.broker import rabbitmq
from app.infrastructure.cache.cache import redis
from app.infrastructure.db.database import database
from app.infrastructure.outbox import OutboxPublisher


logger = structlog.get_logger(__name__)
outbox_publisher = OutboxPublisher(database, rabbitmq, config)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.connect()
    await database.ping()
    await rabbitmq.start()
    logger.info("Broker connection established.")
    await outbox_publisher.start()
    await redis.start()
    await redis.ping()

    yield

    await outbox_publisher.stop()
    await redis.stop()
    await rabbitmq.stop()
    await database.disconnect()



def create_service() -> FastAPI:
    service = FastAPI(
        title="Payment Service",
        docs_url="/inspection/docs",
        redoc_url="/inspection/redoc",
        openapi_url="/inspection/openapi.json",
        lifespan=lifespan
    )

    service.include_router(payments_router, prefix="/api/v1")
    service.include_router(health_router)

    service.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return service
