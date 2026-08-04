from uvicorn import run

from app.core.config import config
from app.core.logging import configure_logging
from app.core.service import create_service


configure_logging()


app = create_service()


if __name__ == "__main__":
    run(
        app=app,
        host=config.APP_HOST,
        port=config.APP_PORT,
        reload=False,
        workers=config.APP_WORKERS,
        forwarded_allow_ips="*",
        log_level="info",
    )
