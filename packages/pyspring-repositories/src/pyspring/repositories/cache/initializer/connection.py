"""
缓存连接初始化器

在应用启动时测试缓存连接（服务已由 Factory 创建和配置）
"""

from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.lifecycle.initializer import IStartupInitializer
from pyspring.core.log.instance import logger

from ..manager import CacheManagerService


@Component
class CacheConnectionInitializer(IStartupInitializer):
    """
    缓存连接初始化器

    职责：
    - 从 CacheManagerService 获取 provider（已由 CacheServiceFactory 配置）
    - 建立连接（如果 provider 支持 connect 方法）
    - 测试缓存连接是否正常
    - 不需要关心具体是什么缓存（Redis/Memory）
    """

    def __init__(self, cache_manager: CacheManagerService):
        """
        Args:
            cache_manager: 缓存管理服务（自动注入，已包含配置好的 provider）
        """
        super().__init__(enabled=True)
        self.cache_manager = cache_manager

    async def initialize(self) -> bool:
        """
        触发缓存服务创建

        从 Manager 获取 provider，触发 Factory 的检测和创建流程。
        Factory 已完成 ping 测试和自动降级，这里获取到的是可用实例。

        Returns:
            bool: 是否成功获取实例
        """
        try:
            # 触发调用链：Initializer → Manager → Factory（全异步）
            # Factory 会进行 ping 检测和自动降级
            provider = await self.cache_manager.provider()

            # 如果 provider 支持 connect 方法，建立连接（鸭子类型）
            connect_method = getattr(provider, "connect", None)
            if connect_method is not None:
                await connect_method()
                logger.info("🔗 缓存连接已建立")

            logger.info("✅ 缓存服务已就绪")
            return True

        except Exception as e:
            logger.error(f"❌ 缓存服务获取失败: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def get_name(self) -> str:
        return "CacheConnectionInitializer"


__all__ = ["CacheConnectionInitializer"]
