"""
数据库连接初始化器

在应用启动时测试数据库连接（服务已由 Factory 创建和配置）
"""
from pyspring.core.ioc.annotations.component import Component
from pyspring.core.ioc.lifecycle.initializer import IStartupInitializer
from pyspring.core.log.instance import logger

from ..manager import DBManagerService


@Component
class DBConnectionInitializer(IStartupInitializer):
    """
    数据库连接初始化器
    
    职责：
    - 从 DBManagerService 获取 provider（已由 DBServiceFactory 配置）
    - 测试数据库连接是否正常
    - 不需要关心具体是什么数据库（PostgreSQL/SQLite/MySQL）
    """

    def __init__(self, db_manager: DBManagerService):
        """
        Args:
            db_manager: 数据库管理服务（自动注入，已包含配置好的 provider）
        """
        super().__init__(enabled=True)
        self.db_manager = db_manager

    async def initialize(self) -> bool:
        """
        触发数据库服务创建
        
        从 Manager 获取 provider，触发 Factory 的检测和创建流程。
        Factory 已完成 ping 测试和自动降级，这里获取到的是可用实例。
        
        Returns:
            bool: 是否成功获取实例
        """
        try:
            # 触发调用链：Initializer → Manager → Factory（全异步）
            # Factory 会进行 ping 检测和自动降级
            provider = await self.db_manager.provider()

            logger.info("✅ 数据库服务已就绪")
            return True

        except Exception as e:
            logger.error(f"❌ 数据库服务获取失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def get_name(self) -> str:
        return "DBConnectionInitializer"


__all__ = ["DBConnectionInitializer"]
