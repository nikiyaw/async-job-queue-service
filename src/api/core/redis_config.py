import redis
import os

# Prefer a specifically named REDIS_URL env var; fallback to CELERY_BROKER_URL if present,
# and to the Docker default 'redis' host if nothing is set.
REDIS_URL = os.environ.get("REDIS_URL", os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0"))

# Create the Redis client
redis_client = redis.from_url(REDIS_URL)