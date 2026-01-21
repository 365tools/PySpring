"""
数据库服务工厂（根据配置选择实现）
"""
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.log.instance import logger
from .config import DatabaseConfig
from .providers.postgres.services.service import PostgresService
from .providers.sqlite.services.service import SqliteService


@Component()
@Singleton
class DBServiceFactory:
    """数据库服务工厂（由 IOC 容器管理）"""

    def __init__(self, database_config: DatabaseConfig, sqlite_service: SqliteService, postgres_service: PostgresService):
        """
        通过 IOC 注入配置和所有服务实现
        
        Args:
            database_config: DatabaseConfig 实例（自动注入）
            sqlite_service: SqliteService 实例（自动注入）
            postgres_service: PostgresService 实例（自动注入）
        """
        self.config: DatabaseConfig = database_config
        self.sqlite_service: SqliteService = sqlite_service
        self.postgres_service: PostgresService = postgres_service

    def get_service(self) -> 'IDatabaseService':
        """
        根据配置返回正确的数据库服务
        
        Returns:
            IDatabaseService: SQLite 或 PostgreSQL 实现
        """
        db_type = self.config.type.lower()

        if db_type == "sqlite":
            logger.debug("DBServiceFactory: Using SqliteService")
            return self.sqlite_service
        elif db_type == "postgresql":
            logger.debug("DBServiceFactory: Using PostgresService")
            return self.postgres_service
        else:
            raise ValueError(f"Unsupported database type: {db_type}. Use 'sqlite' or 'postgresql'.")
