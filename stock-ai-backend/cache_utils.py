import hashlib
import json
import logging
import os
from datetime import date, datetime
from decimal import Decimal
from functools import wraps
from typing import Optional

import redis


logger = logging.getLogger(__name__)

# Redis Configuration (default to local Docker)
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0


def _json_fallback(value):
    """Serialize non-JSON-native objects for cache storage/keying."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def get_redis_client() -> Optional[redis.Redis]:
    """
    Get a Redis client connection.
    Returns None if connection fails.
    """
    if os.getenv("SIMULATE_REDIS_DOWN", "").strip().lower() in {"1", "true", "yes"}:
        logger.warning("Redis down simulation enabled. Caching disabled.")
        return None

    try:
        client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_timeout=2,  # Fast fail
        )
        if client.ping():
            return client
    except redis.ConnectionError:
        logger.warning("Redis connection failed. Caching disabled.")
        return None
    except Exception as e:
        logger.error("Redis error: %s", e)
        return None
    return None


def cached_query(ttl=300):
    """
    Decorator to cache function results in Redis.
    Args:
        ttl (int): Time-to-live in seconds (default 5 mins)
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Check if Redis is available
            r = get_redis_client()
            if not r:
                return func(*args, **kwargs)

            try:
                # 2. Generate canonical cache key
                key_payload = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs,
                }
                key_data = json.dumps(key_payload, sort_keys=True, default=_json_fallback)
                cache_key = hashlib.md5(key_data.encode()).hexdigest()

                # 3. Check cache
                cached_data = r.get(cache_key)
                if cached_data:
                    logger.info("Cache HIT for key: %s", cache_key)
                    print(f"[CACHE] HIT: {cache_key}")
                    try:
                        return json.loads(cached_data)
                    except json.JSONDecodeError:
                        # Corrupt cache entry: delete and continue as miss.
                        r.delete(cache_key)

                # 4. Cache MISS - execute function
                logger.info("Cache MISS for key: %s", cache_key)
                print(f"[CACHE] MISS: {cache_key}")
                result = func(*args, **kwargs)

                # 5. Store result
                if result:
                    try:
                        r.setex(cache_key, ttl, json.dumps(result, default=_json_fallback))
                    except Exception as cache_write_error:
                        logger.error("Cache write error: %s", cache_write_error)

                return result

            except Exception as e:
                # Fallback to function execution on any cache error
                logger.error("Cache error: %s", e)
                return func(*args, **kwargs)

        return wrapper

    return decorator

