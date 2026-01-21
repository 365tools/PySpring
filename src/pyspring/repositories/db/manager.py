from typing import Optional

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.log.instance import logger
from .service import IDBService


class DBManagerService(ISingletonService):
    """
    数据库管理服务
    
    注意:
    - 数据库连接需要通过 ConnectionInitializer 在应用启动时初始化
    - 不再支持延迟初始化，必须先调用 ConnectionInitializer.initialize()
    """

    def __init__(self):
        super().__init__()
        # 默认为 None，由 ConnectionInitializer 设置实际使用的服务
        self.provider: Optional[IDBService] = None

    def set_provider(self, provider: IDBService):
        """设置实际使用的数据库服务提供者"""
        self.provider = provider
        logger.debug(f"✅ DBManager: Provider set to {provider.__class__.__name__}")

    async def service(self) -> IDBService:
        """
        获取已初始化的数据库服务实例
        
        注意: 必须先通过 ConnectionInitializer 初始化
        
        Returns:
            数据库服务实例
            
        Raises:
            RuntimeError: 如果数据库未初始化
        """
        if self.provider is None:
            raise RuntimeError(
                "数据库服务未初始化！请在应用启动时调用 ConnectionInitializer.initialize()"
            )

        # logger.debug(f"✅ db({self.provider}) instance ready.")
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
                logger.debug(f"🔌 DBManager: {self.provider.__class__.__name__} 连接已关闭")
            except Exception as e:
                logger.error(f"🚨 关闭数据库连接失败: {e}")
            finally:
                self.provider = None
