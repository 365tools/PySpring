"""
缓存管理服务

管理缓存服务提供者，支持 Redis 和内存缓存
"""
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
    
    通过 CacheServiceFactory 获取已验证的缓存实例
    """

    def __init__(self, cache_service_factory: CacheServiceFactory):
        """
        通过 IOC 注入工厂
        
        Args:
            cache_service_factory: CacheServiceFactory 实例（自动注入）
        """
        super().__init__()
        self.factory: CacheServiceFactory = cache_service_factory

    async def provider(self) -> ICacheService:
        """
        获取缓存服务（Factory 内部已实现单例）
        
        Factory 已完成连接检测和降级，返回已验证的实例
        
        Returns:
            ICacheService: Redis 或 Memory 实现
        """
        return await self.factory.get_service()

    # Proxy methods to provider
    async def get(self, *args, **kwargs):
        """获取缓存"""
        provider = await self.provider()
        return await provider.get(*args, **kwargs)

    async def set(self, *args, **kwargs):
        """设置缓存"""
        provider = await self.provider()
        return await provider.set(*args, **kwargs)

    async def exists(self, *args, **kwargs):
        """检查键是否存在"""
        provider = await self.provider()
        return await provider.exists(*args, **kwargs)

    async def delete(self, *args, **kwargs):
        """删除缓存"""
        provider = await self.provider()
        return await provider.delete(*args, **kwargs)

    async def scan(self, *args, **kwargs):
        """扫描缓存键（如果支持）"""
        provider = await self.provider()
        if hasattr(provider, 'scan'):
            return await provider.scan(*args, **kwargs)
        raise NotImplementedError(f"{provider.__class__.__name__} does not support scan operation")

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
        provider_instance = await self.provider()
        if provider_instance:
            if hasattr(provider_instance, 'close'):
                try:
                    await provider_instance.close()
                    logger.debug(f"CacheManager: {provider_instance.__class__.__name__} closed")
                except Exception as e:
                    logger.error(f"Failed to close {provider_instance.__class__.__name__}: {e}")
            elif hasattr(provider_instance, 'clear'):
                try:
                    await provider_instance.clear()
                    logger.debug(f"CacheManager: {provider_instance.__class__.__name__} cleared")
                except Exception as e:
                    logger.error(f"Failed to clear {provider_instance.__class__.__name__}: {e}")
