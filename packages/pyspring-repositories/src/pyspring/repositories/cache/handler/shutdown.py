"""
缓存关闭处理器

在应用关闭时释放缓存资源
"""

from pyspring.core.ioc.lifecycle.shutdown import IShutdownHandler
from pyspring.core.log.instance import logger

from ..manager import CacheManagerService


class CacheShutdownHandler(IShutdownHandler):
    """缓存连接关闭处理器"""

    def __init__(self, cache_manager: CacheManagerService, enabled: bool = True):
        super().__init__()
        self.cache_manager = cache_manager
        self.enabled = enabled

    async def shutdown(self) -> bool:
        """关闭缓存连接"""
        try:
            # 检查 Factory 单例，避免触发延迟初始化
            if self.cache_manager and self.cache_manager.factory._service is not None:
                await self.cache_manager.close()
                logger.info("Cache connection closed")
                return True
            else:
                logger.debug("Cache not initialized, skip closing")
                return True
        except Exception as e:
            logger.error(f"Failed to close cache connection: {e}")
            return False

    def get_name(self) -> str:
        return "CacheShutdownHandler"


__all__ = ["CacheShutdownHandler"]
