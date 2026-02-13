import os
import json
import hashlib
from typing import Any, Optional
from utils.logging_config import logger

class CacheService:
    def __init__(self):
        self.redis_client = None
        self.ttl = int(os.getenv("CACHE_TTL", "60"))
        self._init_redis()

    def _init_redis(self):
        try:
            import redis
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            self.redis_client = redis.Redis(host=host, port=port, db=0, socket_timeout=2)
            self.redis_client.ping()
            logger.info(f"Redis connected to {host}:{port}")
        except Exception as e:
            logger.warning(f"Real Redis unavailable: {e}. Attempting FakeRedis fallback.")
            try:
                import fakeredis
                self.redis_client = fakeredis.FakeStrictRedis()
                logger.info("Using FakeRedis in-memory fallback")
            except Exception as fe:
                self.redis_client = None
                logger.error(f"Redis and FakeRedis unavailable: {fe}")

    def make_key(self, prefix: str, payload: dict) -> str:
        try:
            s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        except Exception:
            s = str(payload)
        h = hashlib.sha256(s.encode("utf-8")).hexdigest()
        return f"{prefix}:{h}"

    def get(self, key: str) -> Optional[dict]:
        if not self.redis_client:
            return None
        try:
            cached = self.redis_client.get(key)
            if cached:
                logger.info(f"CACHE HIT: {key}")
                return json.loads(cached.decode("utf-8"))
            logger.info(f"CACHE MISS: {key}")
        except Exception as e:
            logger.error(f"Redis GET error for {key}: {e}")
        return None

    def set(self, key: str, value: dict, ttl: Optional[int] = None):
        if not self.redis_client:
            return
        try:
            self.redis_client.setex(
                key, 
                ttl or self.ttl, 
                json.dumps(value)
            )
            logger.info(f"CACHE SET: {key} (TTL: {ttl or self.ttl}s)")
        except Exception as e:
            logger.error(f"Redis SET error for {key}: {e}")

cache_service = CacheService()
