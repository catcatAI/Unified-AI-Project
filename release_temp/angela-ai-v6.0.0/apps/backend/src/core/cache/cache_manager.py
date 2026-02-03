import time
from typing import Any


class CacheManager:
    """Manages in-memory caching for frequently accessed data."""

    def __init__(self, default_ttl: int = 300):  # default_ttl in seconds (5 minutes)
        """Initializes the CacheManager.

        Args:
            default_ttl (int): Default time-to-live for cache entries in seconds.

        """
        self._cache: dict[str, dict[str, Any]] = {}
        self.default_ttl = default_ttl
        print(f"CacheManager initialized with default TTL: {default_ttl}s.")

    def set(self, key: str, value: Any, ttl: int | None = None):
        """Stores a value in the cache with an optional time-to-live.

        Args:
            key (str): The cache key.
            value (Any): The value to store.
            ttl (Optional[int]): Time-to-live in seconds. If None, uses default_ttl.

        """
        expiration_time = time.time() + (ttl if ttl is not None else self.default_ttl)
        self._cache[key] = {"value": value, "expires_at": expiration_time}
        print(f"Cache: Set key '{key}' (expires at {expiration_time}).")

    def get(self, key: str) -> Any | None:
        """Retrieves a value from the cache. Returns None if the key is not found or has expired.

        Args:
            key (str): The cache key.

        Returns:
            Optional[Any]: The cached value, or None.

        """
        entry = self._cache.get(key)
        if entry:
            if time.time() < entry["expires_at"]:
                print(f"Cache: Retrieved key '{key}'.")
                return entry["value"]
            del self._cache[key]  # Remove expired entry
            print(f"Cache: Key '{key}' expired and removed.")
        print(f"Cache: Key '{key}' not found or expired.")
        return None

    def delete(self, key: str):
        """Deletes a key from the cache."""
        if key in self._cache:
            del self._cache[key]
            print(f"Cache: Deleted key '{key}'.")

    def clear(self):
        """Clears all entries from the cache."""
        self._cache.clear()
        print("Cache: All entries cleared.")


if __name__ == "__main__":
    # Example Usage
    cache = CacheManager(default_ttl=2)  # 2-second TTL for testing

    print("\n--- Test Set and Get ---")
    cache.set("my_data", {"item": 1, "status": "active"})
    data = cache.get("my_data")
    print(f"Retrieved: {data}")

    print("\n--- Test Expiration ---")
    time.sleep(2.5)  # Wait for cache to expire
    data_expired = cache.get("my_data")
    print(f"Retrieved after expiration: {data_expired}")

    print("\n--- Test Delete ---")
    cache.set("temp_key", "temporary_value")
    print(f"Before delete: {cache.get('temp_key')}")
    cache.delete("temp_key")
    print(f"After delete: {cache.get('temp_key')}")

    print("\n--- Test Clear ---")
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    print(f"Cache size before clear: {len(cache._cache)}")
    cache.clear()
    print(f"Cache size after clear: {len(cache._cache)}")
