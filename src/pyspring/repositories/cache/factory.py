"""
缓存服务工厂（根据配置选择实现）
"""
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.log.instance import logger
from .config import CacheConfig
from .providers.memory.services.service import MemoryService
from .providers.redis.services.service import RedisService


@Component()
@Singleton
class CacheServiceFactory:
    """缓存服务工厂（由 IOC 容器管理）"""

    def __init__(self, cache_config: CacheConfig, redis_service: RedisService, memory_service: MemoryService):
        """
        通过 IOC 注入配置和所有服务实现
        
        Args:
            cache_config: CacheConfig 实例（自动注入）
            redis_service: RedisService 实例（自动注入）
            memory_service: MemoryService 实例（自动注入）
        """
        self.config: CacheConfig = cache_config
        self.redis_service: RedisService = redis_service
        self.memory_service: MemoryService = memory_service

    def get_service(self) -> 'ICacheService':
        """
        根据配置返回正确的缓存服务
        
        Returns:
            ICacheService: Redis 或 Memory 实现
        """
        cache_type = self.config.type.lower()

        if cache_type == "redis":
            logger.debug("CacheServiceFactory: Using RedisService")
            return self.redis_service
        elif cache_type == "memory":
            logger.debug("CacheServiceFactory: Using MemoryService")
            return self.memory_service
        elif cache_type == "auto":
            # 自动模式：优先 Redis，失败则降级 Memory
            logger.debug("CacheServiceFactory: Auto mode - trying Redis first")
            return self.redis_service
        else:
            raise ValueError(f"Unsupported cache type: {cache_type}. Use 'redis', 'memory', or 'auto'.")
