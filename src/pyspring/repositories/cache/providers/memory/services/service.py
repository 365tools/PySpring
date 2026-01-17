import time
from collections import OrderedDict
from typing import Optional, Any

from pyspring.log.instance import logger
from ..interfaces.service import IMemoryService


class MemoryService(IMemoryService):

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = ttl

        # 使用有序字典存储数据，支持按插入顺序排序
        self._store: OrderedDict[str, tuple[Any, Optional[float]]] = OrderedDict()

        logger.debug(f"🔧 MemoryService init (max_size={self.max_size}, default_ttl={self.default_ttl})")

    async def get(self, key: str) -> Optional[Any]:
        try:
            # 检查键是否存在
            if key not in self._store:
                return None

            value, expire_at = self._store[key]

            # 检查是否过期
            if expire_at is not None and time.time() > expire_at:
                # 过期则删除
                del self._store[key]
                return None

            # 移动到末尾表示最近使用
            self._store.move_to_end(key)
            return value
        except Exception as e:
            logger.error(f"🚨 获取数据失败: {e}")
            return None

    async def save(self, key: str, value: Any, ttl: Optional[int] = None) -> Any:
        try:
            # 如果达到最大容量，删除最旧的
            if len(self._store) >= self.max_size:
                self._store.popitem(last=False)

            # 计算过期时间戳（如果设置了 TTL）
            expire_at = time.time() + ttl if ttl is not None else None
            self._store[key] = (value, expire_at)
            # 移动到末尾表示最近使用
            self._store.move_to_end(key)
            return True
        except Exception as e:
            logger.error(f"🚨 保存数据失败: {e}")
            return False

    async def set(self, key: str, value: Any, ex: int = None) -> bool:
        """设置缓存（支持过期时间），兼容 Redis 原生 API"""
        return await self.save(key, value, ttl=ex)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            if key not in self._store:
                return False

            _, expire_at = self._store[key]

            # 检查是否过期
            if expire_at is not None and time.time() > expire_at:
                # 过期则删除
                del self._store[key]
                return False

            return True
        except Exception as e:
            logger.error(f"🚨 检查键存在失败: {e}")
            return False

    async def update(self, key: str, value: Any, ttl: Optional[int] = None) -> Any:
        return await self.save(key, value, ttl)

    async def delete(self, key: str) -> bool:
        try:
            if key in self._store:
                del self._store[key]
                return True
            return False
        except Exception as e:
            logger.error(f"🚨 删除数据失败: {e}")
            return False

    async def clear(self) -> None:
        self._store.clear()

    async def ping(self) -> bool:
        # 内存服务总是可用
        return True
