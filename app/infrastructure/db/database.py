from app.core.config import config
from app.infrastructure.db.connection import PostgresConnectionClient


database = PostgresConnectionClient(config)
