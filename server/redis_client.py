import redis
from decouple import config

# Initialize Redis client with values from environment variables
redis_client = redis.Redis(
    host=config('REDIS_HOST', default='localhost'),
    port=config('REDIS_PORT', default=6379, cast=int),
    db=config('REDIS_DB', default=0, cast=int)
)