from typing import Optional

from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.interfaces.core import IManaged
from pyspring.log.instance import logger
from .factory import DBServiceFactory
from .service import IDBService


@Component()
@Singleton
class DBManagerService(IManaged):
    """
    数据库管理服务（由 IOC 容器管理单例）
    
    通过 DBServiceFactory 自动选择数据库实现
    """

    def __init__(self, db_service_factory: DBServiceFactory):
        """
        通过 IOC 注入工厂
        
        Args:
            db_service_factory: DBServiceFactory 实例（自动注入）
        """
        super().__init__()
        self.factory: DBServiceFactory = db_service_factory
        self._provider: Optional[IDBService] = None

    @property
    def provider(self) -> IDBService:
        """
        延迟获取数据库服务（首次调用时从工厂获取）
        
        Returns:
            IDBService: SQLite 或 PostgreSQL 实现
        """
        if self._provider is None:
            self._provider = self.factory.get_service()
            logger.debug(f"DBManager: Provider initialized to {self._provider.__class__.__name__}")
        return self._provider

    async def service(self) -> IDBService:
        """
        获取已初始化的数据库服务实例
        
        Returns:
            数据库服务实例
        """
        return self.provider

    async def session(self):
        """
        便捷方法: 直接获取数据库会话

        使用方式:
            async with db_manager.get_session() as session:
                # 数据库操作

        Returns:
            异步上下文管理器, 用于数据库会话
        """
        db_service = await self.service()
        return await db_service.session()

    async def engine(self):
        """
        获取数据库引擎
        """
        db_service = await self.service()
        return await db_service.engine()

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
        if self.provider:
            try:
                await self.provider.close()
                logger.debug(f"DBManager: {self.provider.__class__.__name__} connection closed")
            except Exception as e:
                logger.error(f"Failed to close database connection: {e}")
            finally:
                self.provider = None