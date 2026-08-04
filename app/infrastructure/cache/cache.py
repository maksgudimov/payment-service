from app.core.config import config
from app.infrastructure.cache.connection import RedisConnectionClient


redis = RedisConnectionClient(config)
