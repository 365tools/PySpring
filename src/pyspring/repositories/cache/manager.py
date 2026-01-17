from typing import Optional

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.log.instance import logger
from .service import ICacheService


class CacheManagerService(ISingletonService):
    """
    缓存管理服务
    
    注意: 
    - 缓存服务需要通过 ConnectionInitializer 在应用启动时初始化
    - 不再支持延迟初始化，必须先调用 ConnectionInitializer.initialize()
    """
    
    def __init__(self):
        super().__init__()
        # 默认为 memory，由 ConnectionInitializer 设置实际使用的服务
        self.provider: Optional[ICacheService] = None

    def set_provider(self, provider: ICacheService):
        """设置实际使用的缓存服务提供者"""
        self.provider = provider
        logger.debug(f"✅ CacheManager: Provider set to {provider.__class__.__name__}")

    async def service(self) -> ICacheService:
        """
        获取已初始化的缓存服务
        
        注意: 必须先通过 ConnectionInitializer 初始化
        
        Returns:
            缓存服务实例
        """
        if self.provider is None:
            raise RuntimeError(
                "缓存服务未初始化！请在应用启动时调用 ConnectionInitializer.initialize()"
            )

        # logger.debug(f"✅ cache({self.provider}) instance ready.")
        return self.provider

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
        if self.provider:
            # 尝试关闭服务
            if hasattr(self.provider, 'close'):
                try:
                    await self.provider.close()
                    logger.debug(f"🔌 CacheManager: {self.provider.__class__.__name__} 连接已关闭")
                except Exception as e:
                    logger.error(f"🚨 关闭 {self.provider.__class__.__name__} 失败: {e}")
            elif hasattr(self.provider, 'clear'):
                try:
                    await self.provider.clear()
                    logger.debug(f"🔌 CacheManager: {self.provider.__class__.__name__} 已清空")
                except Exception as e:
                    logger.error(f"🚨 清理 {self.provider.__class__.__name__} 失败: {e}")

        # 重置实例
        self.provider = None
