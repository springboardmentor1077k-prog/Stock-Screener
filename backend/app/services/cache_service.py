import json
import redis
from app.core.config import settings


class CacheService:

    def __init__(self):
        self.client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get(self, key: str):
        try:
            value = self.client.get(key)
            if value:
                print("⚡ Cache hit:", key)
                return json.loads(value)
        except Exception as e:
            print("Redis get failed:", e)
        return None

    def set(self, key: str, value: dict, ttl: int = 300):
        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            print("💾 Cached:", key)
        except Exception as e:
            print("Redis set failed:", e)