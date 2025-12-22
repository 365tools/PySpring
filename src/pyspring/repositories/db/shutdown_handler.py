"""
数据库关闭处理器

在应用关闭时关闭数据库连接
"""
from pyspring.interfaces.IShutdownHandler import IShutdownHandler
from pyspring.log.loguru.ins import logger
from pyspring.repositories.db.manager import DBManagerService


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
            if self.db_manager and self.db_manager.ins:
                await self.db_manager.close()
                logger.info("💾 数据库连接已关闭")
                return True
            else:
                logger.debug("⏭️  数据库未初始化，无需关闭")
                return True
        except Exception as e:
            logger.error(f"❌ 关闭数据库连接失败: {e}")
            return False

    def get_name(self) -> str:
        """
        Returns:
            关闭处理器名称
        """
        return "数据库连接关闭处理器"
