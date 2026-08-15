"""
数据库关闭处理器

在应用关闭时关闭数据库连接
"""
from pyspring.core.ioc.lifecycle.shutdown import IShutdownHandler
from pyspring.core.log.instance import logger

from ..manager import DBManagerService


class DBShutdownHandler(IShutdownHandler):
    """
    数据库连接关闭处理器
    
    在应用关闭时关闭数据库连接池，释放资源
    """

    def __init__(self, db_manager: DBManagerService, enabled: bool = True):
        """
        Args:
            db_manager: DBManagerService 实例
            enabled: 是否启用关闭处理
        """
        super().__init__()
        self.db_manager = db_manager
        self.enabled = enabled

    async def shutdown(self) -> bool:
        """
        关闭数据库连接
        
        Returns:
            bool: 是否成功关闭
        """
        try:
            # 检查 Factory 单例，避免触发延迟初始化
            if self.db_manager and self.db_manager.factory._service is not None:
                await self.db_manager.close()
                logger.info("Database connection closed")
                return True
            else:
                logger.debug("Database not initialized, skip closing")
                return True
        except Exception as e:
            logger.error(f"Failed to close database connection: {e}")
            return False

    def get_name(self) -> str:
        """
        Returns:
            关闭处理器名称
        """
        return "数据库连接关闭处理器"
