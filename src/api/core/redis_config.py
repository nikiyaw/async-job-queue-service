import redis
import os

# We will use an environment variable for the Redis URL in a more advanced setup.
# For now, we'll hardcode it to match our docker-compose file.
REDIS_URL = "redis://localhost:6379"

# Create the Redis client
redis_client = redis.from_url(REDIS_URL)