"""
内存缓存服务实现
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.log.instance import logger

from ....config import CacheConfig
from ..interfaces.service import IMemoryService


@Component
@Singleton
class MemoryService(IMemoryService):
    """内存缓存服务（LRU 实现，由 IOC 容器管理）"""

    def __init__(self, cache_config: CacheConfig):
        """
        通过 IOC 注入配置

        Args:
            cache_config: CacheConfig 实例（自动注入）
        """
        self.config: CacheConfig = cache_config

        memory_config = self.config.memory
        self.max_size = memory_config.max_size
        self.default_ttl = memory_config.ttl
        self._store: OrderedDict[str, tuple[Any, (float) | None]] = OrderedDict()

        logger.debug(f"MemoryService initialized (max_size={self.max_size}, default_ttl={self.default_ttl}s)")

    async def get(self, key: str) -> (Any) | None:
        try:
            if key not in self._store:
                return None

            value, expire_at = self._store[key]

            if expire_at is not None and time.time() > expire_at:
                del self._store[key]
                return None

            self._store.move_to_end(key)
            return value
        except Exception as e:
            logger.error(f"Get failed: {e}")
            return None

    async def save(self, key: str, value: Any, ttl: (int) | None = None) -> Any:
        try:
            if len(self._store) >= self.max_size:
                self._store.popitem(last=False)

            expire_at = time.time() + ttl if ttl is not None else None
            self._store[key] = (value, expire_at)
            self._store.move_to_end(key)
            return True
        except Exception as e:
            logger.error(f"Save failed: {e}")
            return False

    async def set(self, key: str, value: Any, ex: (int) | None = None) -> bool:
        """设置缓存，支持过期时间"""
        return await self.save(key, value, ttl=ex)

    async def exists(self, key: str) -> bool:
        try:
            if key not in self._store:
                return False

            _, expire_at = self._store[key]

            if expire_at is not None and time.time() > expire_at:
                del self._store[key]
                return False

            return True
        except Exception as e:
            logger.error(f"Check exists failed: {e}")
            return False

    async def update(self, key: str, value: Any, ttl: (int) | None = None) -> Any:
        return await self.save(key, value, ttl)

    async def delete(self, key: str) -> bool:
        try:
            if key in self._store:
                del self._store[key]
                return True
            return False
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    async def clear(self) -> None:
        self._store.clear()

    async def ping(self) -> bool:
        return True
