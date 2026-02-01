"""
数据库服务工厂（根据配置选择实现）
"""
from typing import Optional

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.log.instance import logger
from .config import DatabaseConfig
from .providers.postgres.services.service import PostgresService
from .providers.sqlite.services.service import SqliteService
from .providers.mysql.services.service import MysqlService
from .service import IDBService


@Component
@Singleton
class DBServiceFactory:
    """数据库服务工厂（由 IOC 容器管理）"""

    def __init__(self, database_config: DatabaseConfig):
        """
        通过 IOC 注入配置
        
        Args:
            database_config: DatabaseConfig 实例（自动注入）
        """
        self.config: DatabaseConfig = database_config
        self._service: Optional[IDBService] = None
        self._service_type: Optional[str] = None
        
        # 注册所有支持的服务创建器（使用 lambda 实现延迟加载）
        self._service_creators = {
            "sqlite": lambda: self._create_sqlite_service(),
            "postgresql": lambda: self._create_postgres_service(),
            "mysql": lambda: self._create_mysql_service(),
        }

    async def get_service(self) -> IDBService:
        """
        根据配置返回正确的数据库服务（单例模式）
        
        Returns:
            IDBService: SQLite 或 PostgreSQL 实现
        """
        # 如果已创建，直接返回（单例）
        if self._service is not None:
            return self._service

        db_type = self.config.type.lower()

        if db_type in self._service_creators:
            self._service = self._service_creators[db_type]()
            self._service_type = db_type
        elif db_type == "auto":
            # auto 模式：默认 PostgreSQL，失败降级到 MySQL，最后降级到 SQLite
            logger.debug("DBServiceFactory: Auto mode - trying PostgreSQL first...")
            self._service = await self._try_postgres_or_mysql_or_fallback()
        else:
            available_types = list(self._service_creators.keys()) + ["auto"]
            raise ValueError(f"Unsupported database type: {db_type}. Available types: {', '.join(available_types)}.")

        return self._service

    def _create_sqlite_service(self) -> SqliteService:
        """创建 SQLite 服务"""
        logger.info("✅ 使用 SQLite 数据库")
        return SqliteService(self.config)

    def _create_postgres_service(self) -> PostgresService:
        """创建 PostgreSQL 服务"""
        logger.info("✅ 使用 PostgreSQL 数据库")
        return PostgresService(self.config)

    def _create_mysql_service(self) -> MysqlService:
        """创建 MySQL 服务"""
        logger.info("✅ 使用 MySQL 数据库")
        return MysqlService(self.config)

    async def _try_postgres_or_mysql_or_fallback(self) -> IDBService:
        """
        尝试连接 PostgreSQL，失败则降级到 MySQL，再失败则降级到 SQLite
        
        策略：
        1. 检查 PostgreSQL 配置完整性
        2. 创建 PostgreSQL 服务并执行 ping 测试
        3. PostgreSQL 测试成功：返回 PostgreSQL
        4. PostgreSQL 测试失败：尝试 MySQL
        5. MySQL 测试成功：返回 MySQL
        6. MySQL 测试失败：降级到 SQLite
        
        Returns:
            IDBService: PostgreSQL、MySQL 或 SQLite 服务（已测试可用）
        """
        # 1. 检查配置完整性
        pg_config = self.config.postgresql
        if not (pg_config.host and pg_config.database and pg_config.user):
            logger.warning("⚠️ PostgreSQL 配置不完整，尝试 MySQL...")
            return await self._try_mysql_or_fallback()

        # 2. 创建并测试 PostgreSQL 服务
        try:
            logger.info("🔍 Auto 模式：测试 PostgreSQL 连接...")
            service = PostgresService(self.config)

            # 执行异步 ping 测试
            is_connected = await service.ping()

            if is_connected:
                logger.info("✅ PostgreSQL 连接成功，使用 PostgreSQL")
                self._service_type = "postgresql"
                return service
            else:
                logger.warning("⚠️ PostgreSQL 连接失败，尝试 MySQL...")
                return await self._try_mysql_or_fallback()

        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL 初始化失败，尝试 MySQL: {e}")
            return await self._try_mysql_or_fallback()

    async def _try_mysql_or_fallback(self) -> IDBService:
        """
        尝试连接 MySQL，失败则降级到 SQLite
        
        策略：
        1. 检查 MySQL 配置完整性
        2. 创建 MySQL 服务并执行 ping 测试
        3. 测试成功：返回 MySQL
        4. 测试失败或配置不完整：降级到 SQLite
        
        Returns:
            IDBService: MySQL 或 SQLite 服务（已测试可用）
        """
        # 1. 检查配置完整性
        mysql_config = self.config.mysql
        if not (mysql_config.host and mysql_config.database and mysql_config.user):
            logger.warning("⚠️ MySQL 配置不完整，降级到 SQLite")
            self._service_type = "sqlite"
            return self._create_sqlite_service()

        # 2. 创建并测试 MySQL 服务
        try:
            logger.info("🔍 Auto 模式：测试 MySQL 连接...")
            service = MysqlService(self.config)

            # 执行异步 ping 测试
            is_connected = await service.ping()

            if is_connected:
                logger.info("✅ MySQL 连接成功，使用 MySQL")
                self._service_type = "mysql"
                return service
            else:
                logger.warning("⚠️ MySQL 连接失败，降级到 SQLite")
                self._service_type = "sqlite"
                return self._create_sqlite_service()

        except Exception as e:
            logger.warning(f"⚠️ MySQL 初始化失败，降级到 SQLite: {e}")
            self._service_type = "sqlite"
            return self._create_sqlite_service()
