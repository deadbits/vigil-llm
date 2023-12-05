from collections import OrderedDict
from typing import Any


class LRUCache:
    def __init__(self, capacity: int):
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.capacity = capacity

    def get(self, key: str):
        """get a value from the cache"""
        if key in self.cache:
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None

    def set(self, key: str, value: Any) -> None:
        """sets a key-value pair in the cache"""
        if key in self.cache:
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value

    def empty(self) -> None:
        """empty the cache"""
        self.cache = OrderedDict()
