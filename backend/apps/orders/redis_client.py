import logging
import redis
from django.conf import settings

logger = logging.getLogger(__name__)

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
    try:
        # Decode responses as strings directly for easier JSON parsing
        _redis_client = redis.from_url(
            redis_url, 
            decode_responses=True, 
            socket_timeout=2.0,
            socket_connect_timeout=2.0
        )
        # Test connection
        _redis_client.ping()
        logger.info(f"Successfully connected to Redis at {redis_url}")
        return _redis_client
    except Exception as e:
        logger.warning(f"Failed to connect to Redis at {redis_url}: {e}. Falling back to DB-only notifications.")
        _redis_client = None
        return None
