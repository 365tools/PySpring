from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.annotations.scope import Singleton
from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.log.instance import logger

from .factory import DBServiceFactory
from .service import IDBService


@Component
@Singleton
class DBManagerService(IManaged):
    """
    数据库管理服务（由 IOC 容器管理单例）

    通过 DBServiceFactory 获取已验证的数据库实例
    """

    def __init__(self, db_service_factory: DBServiceFactory):
        """
        通过 IOC 注入工厂

        Args:
            db_service_factory: DBServiceFactory 实例（自动注入）
        """
        super().__init__()
        self.factory: DBServiceFactory = db_service_factory

    async def provider(self) -> IDBService:
        """
        获取数据库服务（Factory 内部已实现单例）

        Factory 已完成连接检测和降级，返回已验证的实例

        Returns:
            IDBService: SQLite 或 PostgreSQL 实现
        """
        return await self.factory.get_service()

    async def service(self) -> IDBService:
        """
        获取已初始化的数据库服务实例

        Returns:
            数据库服务实例
        """
        return await self.provider()

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
        provider_instance = await self.provider()
        if provider_instance:
            try:
                await provider_instance.close()
                logger.debug(f"DBManager: {provider_instance.__class__.__name__} connection closed")
            except Exception as e:
                logger.error(f"Failed to close database connection: {e}")
