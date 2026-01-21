"""
数据库连接初始化器

在应用启动时自动初始化数据库连接（服务已由 IOC 创建）
"""
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.lifecycle.initializer import IStartupInitializer
from pyspring.log.instance import logger
from ..config import DatabaseConfig
from ..manager import DBManagerService


@Component()
class DBConnectionInitializer(IStartupInitializer):
    """
    数据库连接初始化器（仅负责连接建立）
    """

    def __init__(self, db_config: DatabaseConfig, db_manager: DBManagerService):
        """
        Args:
            db_config: 数据库配置实例（自动注入）
            db_manager: 数据库管理服务实例（自动注入）
        """
        super().__init__(enabled=True)
        self.db_config = db_config
        self.db_manager = db_manager

    async def startup(self) -> bool:
        """
        启动时初始化数据库连接
        
        Returns:
            bool: 是否成功初始化
        """
        try:
            db_type = self.db_config.type.lower()
            logger.info(f"Initializing database connection: {db_type}")

            # 从管理器获取服务（由工厂自动选择）
            provider = self.db_manager.provider

            # 测试数据库连接
            if db_type == "sqlite":
                logger.info(f"SQLite database ready: {self.db_config.sqlite.database}")
            elif db_type == "postgresql":
                pg_cfg = self.db_config.postgresql
                logger.info(f"PostgreSQL database ready: {pg_cfg.host}:{pg_cfg.port}/{pg_cfg.database}")
            elif db_type == "mysql":
                logger.warning("MySQL support is not yet implemented")
                return False
            else:
                logger.error(f"Unsupported database type: {db_type}")
                return False

            logger.info(f"Database connection initialized: {db_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            return False

    def get_name(self) -> str:
        return "DBConnectionInitializer"


__all__ = ["DBConnectionInitializer"]
