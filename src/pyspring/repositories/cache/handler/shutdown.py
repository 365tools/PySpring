"""
from pyspring.core.services.system import SystemService
from pyspring.security.authentication.services.session.token import TokenManagerService

缓存关闭处理器

在应用关闭时关闭缓存连接
"""
from pyspring.core.abstracts.interfaces.handler.shutdown import IShutdownHandler
from pyspring.core.services.system import SystemService
from pyspring.log.instance import logger
from pyspring.security.authentication.services.session.token import TokenManagerService
from ..manager import CacheManagerService


class CacheShutdownHandler(IShutdownHandler):
    """
    缓存连接关闭处理器
    
    在应用关闭时关闭缓存连接（Redis/Memory），释放资源
    """

    def __init__(self, cache_manager: CacheManagerService, enabled: bool = True):
        """
        Args:
            cache_manager: CacheManagerService 实例
            enabled: 是否启用关闭处理
        """
        super().__init__(enabled)
        self.cache_manager = cache_manager

    async def shutdown(self) -> bool:
        """
        关闭缓存连接
        
        Returns:
            bool: 是否成功关闭
        """
        try:
            # ✅ 1. 取消 TokenManagerService 的后台任务（如果存在）
            try:
                await TokenManagerService.cancel_background_tasks()
            except Exception as e:
                logger.debug(f"⏭️  取消 Token 后台任务时出现异常（可能未启用）: {e}")

            # ✅ 2. 取消 SystemService 的事件任务（如果存在）
            try:
                await SystemService.cancel_event_tasks()
            except Exception as e:
                logger.debug(f"⏭️  取消事件任务时出现异常（可能未启用）: {e}")

            # ✅ 3. 关闭缓存连接
            if self.cache_manager and self.cache_manager.provider:
                await self.cache_manager.close()
                logger.info("🗄️  缓存连接已关闭")
                return True
            else:
                logger.debug("⏭️  缓存未初始化，无需关闭")
                return True
        except Exception as e:
            logger.error(f"❌ 关闭缓存连接失败: {e}")
            return False

    def get_name(self) -> str:
        """
        Returns:
            关闭处理器名称
        """
        return "缓存连接关闭处理器"
