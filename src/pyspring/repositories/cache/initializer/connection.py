"""
缓存连接初始化器

在应用启动时初始化缓存连接（服务已由 IOC 创建）
"""
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.lifecycle.initializer import IStartupInitializer
from pyspring.log.instance import logger
from ..config import CacheConfig
from ..manager import CacheManagerService


@Component()
class CacheConnectionInitializer(IStartupInitializer):
    """缓存连接初始化器（仅负责连接建立）"""

    def __init__(self, cache_config: CacheConfig, cache_manager: CacheManagerService):
        super().__init__(enabled=True)
        self.cache_config = cache_config
        self.cache_manager = cache_manager

    async def startup(self) -> bool:
        """初始化缓存连接"""
        try:
            cache_type = self.cache_config.type.lower()

            # 从管理器获取服务（由工厂自动选择）
            provider = self.cache_manager.provider

            # 如果是 Redis，需要建立连接
            if cache_type == "redis":
                if hasattr(provider, 'connect'):
                    await provider.connect()
                    logger.info(f"Redis connection established: {self.cache_config.redis.host}:{self.cache_config.redis.port}")
            elif cache_type == "memory":
                logger.info(f"Memory cache ready (max_size={self.cache_config.memory.max_size}, ttl={self.cache_config.memory.ttl}s)")

            # 测试连接
            if await provider.ping():
                logger.info(f"{cache_type.capitalize()} cache ready")
                return True
            else:
                logger.error(f"{cache_type.capitalize()} ping failed")
                return False

        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
            return False

    def get_name(self) -> str:
        return "CacheConnectionInitializer"


__all__ = ["CacheConnectionInitializer"]
