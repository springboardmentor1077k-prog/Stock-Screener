"""
Simple in-memory caching utilities for the Stock Screener backend.

This module is intentionally lightweight and process-local (no Redis) so it
works out-of-the-box for development and small deployments. For production,
this can be swapped with a Redis-backed implementation without changing
consumer code.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Optional, Dict


@dataclass
class CacheItem:
    value: Any
    expires_at: float


class TTLCache:
    """
    Very small, in-memory TTL cache with a max size.

    - Thread-safe for simple web workloads.
    - On cache miss or expired item, returns None.
    """

    def __init__(self, ttl_seconds: int = 600, max_items: int = 512) -> None:
        self._ttl = ttl_seconds
        self._max_items = max_items
        self._store: Dict[str, CacheItem] = {}
        self._lock = threading.Lock()

    def _prune_expired(self) -> None:
        """Remove expired items; called opportunistically on set()."""
        now = time.time()
        keys_to_delete = [k for k, v in self._store.items() if v.expires_at <= now]
        for k in keys_to_delete:
            self._store.pop(k, None)

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if present and not expired; otherwise None."""
        if key is None:
            return None

        with self._lock:
            item = self._store.get(key)
            if not item:
                return None

            if item.expires_at <= time.time():
                # Expired – remove and treat as miss
                self._store.pop(key, None)
                return None

            return item.value

    def set(self, key: str, value: Any) -> None:
        """Store value under key with TTL."""
        if key is None:
            return

        with self._lock:
            # Best-effort pruning of expired entries
            self._prune_expired()

            # Very simple size control: if we are over capacity, drop oldest entries
            if len(self._store) >= self._max_items:
                # Sort by expiry; drop earliest expiring items first
                for k, _ in sorted(self._store.items(), key=lambda item: item[1].expires_at)[: len(self._store) - self._max_items + 1]:
                    self._store.pop(k, None)

            self._store[key] = CacheItem(value=value, expires_at=time.time() + self._ttl)

    def clear(self) -> None:
        """Clear the entire cache."""
        with self._lock:
            self._store.clear()


# Global cache instances
# ----------------------

# Cache for AI advisor answers keyed by normalized user query string.
ai_advice_cache = TTLCache(ttl_seconds=600, max_items=512)

