from typing import Optional

from pyspring.interfaces.ISingleton import ISingletonService
from pyspring.log.loguru.ins import logger
from pyspring.repositories.cache.memory.impl.service import MemoryService
from pyspring.repositories.cache.redis.impl.service import RedisService
from pyspring.repositories.cache.service import ICacheService


class CacheManagerService(ISingletonService):
    """
    缓存管理服务
    
    注意: 
    - 缓存服务需要通过 CacheInitializer 在应用启动时初始化
    - 不再支持延迟初始化，必须先调用 CacheInitializer.initialize()
    """
    
    def __init__(self, redis: Optional[RedisService] = None, memory: Optional[MemoryService] = None):
        super().__init__()
        self._redis = redis or RedisService()
        self._memory = memory or MemoryService()
        self._use_redis = True
        # 默认为 memory，由 CacheInitializer 设置实际使用的服务
        self.ins: ICacheService = self._memory

    async def service(self) -> ICacheService:
        """
        获取已初始化的缓存服务
        
        注意: 必须先通过 CacheInitializer 初始化
        
        Returns:
            缓存服务实例
        """
        if self.ins is None:
            raise RuntimeError(
                "缓存服务未初始化！请在应用启动时调用 CacheInitializer.initialize()"
            )

        logger.debug(f"✅ cache({self.ins}) instance ready.")
        return self.ins

    @staticmethod
    def key(*args, **kwargs) -> str:
        """生成缓存键"""
        if args:
            return "::".join(str(arg) for arg in args)
        if kwargs:
            return "::".join([str(kwargs[key]) for key in kwargs.keys()])
        return ""

    async def close(self) -> None:
        """关闭所有缓存连接，释放资源"""
        try:
            if self._redis is not None:
                await self._redis.close()
                logger.debug("🔌 CacheManager: Redis 连接已关闭")
        except Exception as e:
            logger.error(f"🚨 关闭 Redis 连接失败: {e}")

        try:
            if self._memory is not None:
                await self._memory.clear()
                logger.debug("🔌 CacheManager: Memory 缓存已清空")
        except Exception as e:
            logger.error(f"🚨 清理 Memory 缓存失败: {e}")

        # 重置为默认 memory 实例
        self.ins = self._memory
