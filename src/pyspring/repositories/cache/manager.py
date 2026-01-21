"""
缓存管理服务

管理缓存服务提供者，支持 Redis 和内存缓存
"""
from typing import Optional

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.interfaces.core import IManaged
from pyspring.log.instance import logger
from .factory import CacheServiceFactory
from .service import ICacheService


@Component()
@Singleton
class CacheManagerService(IManaged):
    """
    缓存管理服务（由 IOC 容器管理单例）
    
    通过 CacheServiceFactory 自动选择缓存实现
    """

    def __init__(self, cache_service_factory: CacheServiceFactory):
        """
        通过 IOC 注入工厂
        
        Args:
            cache_service_factory: CacheServiceFactory 实例（自动注入）
        """
        super().__init__()
        self.factory: CacheServiceFactory = cache_service_factory
        self._provider: Optional[ICacheService] = None

    @property
    def provider(self) -> ICacheService:
        """
        延迟获取缓存服务（首次调用时从工厂获取）
        
        Returns:
            ICacheService: Redis 或 Memory 实现
        """
        if self._provider is None:
            self._provider = self.factory.get_service()
            logger.debug(f"CacheManager: Provider initialized to {self._provider.__class__.__name__}")
        return self._provider

    @staticmethod
    def key(*args, **kwargs) -> str:
        """生成缓存键"""
        if args:
            return "::".join(str(arg) for arg in args)
        if kwargs:
            return "::".join([str(kwargs[key]) for key in kwargs.keys()])
        return ""

    async def close(self) -> None:
        """关闭缓存连接"""
        if self.provider:
            if hasattr(self.provider, 'close'):
                try:
                    await self.provider.close()
                    logger.debug(f"CacheManager: {self.provider.__class__.__name__} closed")
                except Exception as e:
                    logger.error(f"Failed to close {self.provider.__class__.__name__}: {e}")
            elif hasattr(self.provider, 'clear'):
                try:
                    await self.provider.clear()
                    logger.debug(f"CacheManager: {self.provider.__class__.__name__} cleared")
                except Exception as e:
                    logger.error(f"Failed to clear {self.provider.__class__.__name__}: {e}")

        self.provider = None