import redis
from .settings import settings

# Create the Redis client
redis_client = redis.from_url(settings.redis_url)