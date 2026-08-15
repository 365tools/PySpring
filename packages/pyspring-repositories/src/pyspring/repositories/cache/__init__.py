"""
缓存模块

提供 Redis、内存和 Memcached 缓存支持
"""
from .config import CacheConfig, RedisConfig, MemoryConfig, MemcachedConfig
from .initializer import CacheConnectionInitializer
from .manager import CacheManagerService
from .service import ICacheService

__all__ = [
    "CacheConfig",
    "RedisConfig",
    "MemoryConfig",
    "MemcachedConfig",
    "CacheManagerService",
    "ICacheService",
    "CacheConnectionInitializer",
]
