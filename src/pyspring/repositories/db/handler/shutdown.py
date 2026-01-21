"""
数据库关闭处理器

在应用关闭时关闭数据库连接
"""
from pyspring.ioc.lifecycle.shutdown import IShutdownHandler
from pyspring.log.instance import logger
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
        super().__init__(enabled)
        self.db_manager = db_manager

    async def shutdown(self) -> bool:
        """
        关闭数据库连接
        
        Returns:
            bool: 是否成功关闭
        """
        try:
            if self.db_manager and self.db_manager.provider:
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
