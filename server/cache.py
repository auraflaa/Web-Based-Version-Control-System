import json
from functools import wraps
import hashlib
from .logger import get_logger
from .redis_client import redis_client

logger = get_logger(__name__)

# Metrics for cache monitoring
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        
    def increment_hit(self):
        self.hits += 1
        
    def increment_miss(self):
        self.misses += 1

metrics = CacheMetrics()

class Cache:
    def __init__(self, expiration=3600):
        try:
            self.redis = redis_client
            self.expiration = expiration
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise

    def generate_key(self, *args, **kwargs):
        """Generate a cache key from function arguments"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, key):
        """Get value from cache"""
        try:
            value = self.redis.get(key)
            if value:
                metrics.increment_hit()
                return json.loads(value)
            metrics.increment_miss()
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(self, key, value, expire=None):
        """Set value in cache"""
        try:
            if expire is None:
                expire = self.expiration
            self.redis.setex(
                key,
                expire,
                json.dumps(value)
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")

    def delete(self, key):
        """Delete value from cache"""
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")

    def flush(self):
        """Flush all cache entries"""
        try:
            self.redis.flushdb()
            logger.info("Cache flushed successfully")
        except Exception as e:
            logger.error(f"Cache flush error: {e}")

# Initialize cache instance
cache = Cache()

def cached(prefix=""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Generate cache key
            cache_key = f"{prefix}:{cache.generate_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            
            if result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return result
            
            # If not in cache, execute function
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(self, *args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator

def cache_response(expire_time=3600):
    """Decorator for caching Flask route responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [f.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = "response:" + "|".join(key_parts)
            
            # Try to get from cache
            response = cache.get(cache_key)
            if response is not None:
                return response
                
            # Get fresh response
            response = f(*args, **kwargs)
            
            # Cache the response
            cache.set(cache_key, response, expire=expire_time)
            
            return response
        return decorated_function
    return decorator

def cache_file_content(repo_id, file_path, content):
    """Cache file content with repo_id and file_path as key"""
    key = f"file:{repo_id}:{file_path}"
    cache.set(key, content)

def get_cached_file_content(repo_id, file_path):
    """Get cached file content by repo_id and file_path"""
    key = f"file:{repo_id}:{file_path}"
    return cache.get(key)

def invalidate_repo_cache(repo_id):
    """Invalidate all cache entries for a specific repository"""
    try:
        pattern = f"*:{repo_id}:*"
        keys = cache.redis.keys(pattern)
        if keys:
            cache.redis.delete(*keys)
            logger.info(f"Invalidated cache for repo {repo_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate repo cache: {e}")

def get_cache_stats():
    """Get cache statistics"""
    try:
        info = cache.redis.info()
        return {
            'used_memory': info['used_memory'],
            'connected_clients': info['connected_clients'],
            'total_connections_received': info['total_connections_received'],
            'keyspace_hits': info['keyspace_hits'],
            'keyspace_misses': info['keyspace_misses'],
            'local_hits': metrics.hits,
            'local_misses': metrics.misses
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {}