from typing import Optional

from pyspring.interfaces.ISingleton import ISingletonService
from pyspring.log.loguru.ins import logger
from pyspring.repositories.db.postgres.impl.service import PostgresService
from pyspring.repositories.db.service import IDBService
from pyspring.repositories.db.sqlite.impl.service import SqliteService


class DBManagerService(ISingletonService):
    """
    数据库管理服务
    
    注意:
    - 数据库连接需要通过 DBInitializer 在应用启动时初始化
    - 不再支持延迟初始化，必须先调用 DBInitializer.initialize()
    """

    def __init__(self, postgres: Optional[PostgresService] = None, sqlite: Optional[SqliteService] = None):
        super().__init__()
        self._postgres = postgres or PostgresService()
        self._sqlite = sqlite or SqliteService()
        self._use_postgres = True
        # 默认为 None，由 DBInitializer 设置实际使用的服务
        self.ins: Optional[IDBService] = None

    async def service(self) -> IDBService:
        """
        获取已初始化的数据库服务实例
        
        注意: 必须先通过 DBInitializer 初始化
        
        Returns:
            数据库服务实例
            
        Raises:
            RuntimeError: 如果数据库未初始化
        """
        if self.ins is None:
            raise RuntimeError(
                "数据库服务未初始化！请在应用启动时调用 DBInitializer.initialize()"
            )

        logger.debug(f"✅ db({self.ins}) instance ready.")
        return self.ins

    async def get_session(self):
        """
        便捷方法: 直接获取数据库会话

        使用方式:
            async with db_manager.get_session() as session:
                # 数据库操作

        Returns:
            异步上下文管理器, 用于数据库会话
        """
        db_service = await self.service()
        return await db_service.get_session()

    async def get_engine(self):
        """
        获取数据库引擎
        """
        db_service = await self.service()
        return await db_service.get_engine()

    @staticmethod
    def table_name(*args, **kwargs) -> str:
        """
        生成表名(辅助方法)
        """
        if args:
            return "_".join(str(arg) for arg in args)
        if kwargs:
            return "_".join([str(kwargs[key]) for key in kwargs.keys()])
        return ""

    async def close(self) -> None:
        """
        关闭所有数据库连接, 释放资源
        """
        try:
            if self._postgres is not None:
                await self._postgres.close()
                logger.debug("🔌 DBManager: PostgreSQL 连接已关闭")
        except Exception as e:
            logger.error(f"🚨 关闭 PostgreSQL 连接失败: {e}")

        try:
            if self._sqlite is not None:
                await self._sqlite.close()
                logger.debug("🔌 DBManager: SQLite 连接已关闭")
        except Exception as e:
            logger.error(f"🚨 关闭 SQLite 连接失败: {e}")

        self.ins = None
