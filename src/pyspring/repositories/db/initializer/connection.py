"""
数据库连接初始化器

在应用启动时初始化数据库连接（PostgreSQL/SQLite）
"""
from pyspring.core.interfaces.initializer.startup import IStartupInitializer
from pyspring.log.instance import logger
from pyspring.repositories.base.config.loader import RepositoriesConfigManager
from pyspring.repositories.db.manager import DBManagerService


class DBConnectionInitializer(IStartupInitializer):
    """
    数据库连接初始化器
    
    根据配置初始化 PostgreSQL 或 SQLite 数据库连接
    支持自动降级策略
    """

    def __init__(self, db_manager: DBManagerService, enabled: bool = True):
        """
        Args:
            db_manager: 数据库管理服务实例
            enabled: 是否启用该初始化器
        """
        super().__init__(enabled)
        self.db_manager = db_manager
        self.config_manager = RepositoriesConfigManager()

    def get_name(self) -> str:
        return "DBConnectionInitializer"

    async def initialize(self) -> bool:
        """
        初始化数据库连接
        
        流程:
        1. 读取配置（type, fallback_to_sqlite）
        2. 根据配置连接对应的数据库
        3. 失败时根据降级策略处理
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 1. 读取数据库配置
            db_config = self.config_manager.get_database_config()
            db_type = db_config.get('type', 'auto').lower()
            fallback_to_sqlite = db_config.get('fallback_to_sqlite', True)

            logger.debug(f"数据库配置: type={db_type}, fallback={fallback_to_sqlite}")

            # 2. 根据配置初始化
            if db_type == 'sqlite':
                # 强制使用 SQLite
                return await self._init_sqlite()

            elif db_type == 'postgresql':
                # 强制使用 PostgreSQL
                success = await self._init_postgresql()
                if not success and fallback_to_sqlite:
                    logger.warning("PostgreSQL 初始化失败，降级到 SQLite")
                    return await self._init_sqlite()
                return success

            else:  # 'auto' 或其他值
                # 优先 PostgreSQL，失败时降级到 SQLite
                success = await self._init_postgresql()
                if not success:
                    if fallback_to_sqlite:
                        logger.info("PostgreSQL 不可用，使用 SQLite 数据库")
                        return await self._init_sqlite()
                    else:
                        logger.error("PostgreSQL 不可用，且不允许降级到 SQLite")
                        return False
                return True

        except Exception as e:
            logger.error(f"数据库初始化异常: {e}", exc_info=True)
            return False

    async def _init_postgresql(self) -> bool:
        """
        初始化 PostgreSQL 连接
        
        Returns:
            bool: 是否成功
        """
        try:
            from pyspring.repositories.db.ins.postgres.impl.service import PostgresService
            postgres = PostgresService()
            # 测试 PostgreSQL 连接
            if await postgres.ping():
                self.db_manager.set_provider(postgres)
                logger.info(f"✅ PostgreSQL 已连接: {postgres.url}")
                return True
            else:
                logger.debug("PostgreSQL ping 失败")
                await postgres.close()
                return False
        except Exception as e:
            logger.warning(f"PostgreSQL 连接失败: {e}")
            return False

    async def _init_sqlite(self) -> bool:
        """
        初始化 SQLite 连接
        
        Returns:
            bool: 是否成功（SQLite 总是成功）
        """
        try:
            from pyspring.repositories.db.ins.sqlite.impl.service import SqliteService
            sqlite = SqliteService()
            # 测试 SQLite 连接
            if await sqlite.ping():
                self.db_manager.set_provider(sqlite)
                logger.info(f"✅ SQLite 已连接: {sqlite.database}")
                return True
            else:
                logger.error("SQLite ping 失败")
                await sqlite.close()
                return False
        except Exception as e:
            logger.error(f"SQLite 连接失败: {e}")
            return False
