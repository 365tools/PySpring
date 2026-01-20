"""
from sqlalchemy import inspect, text

认证服务初始化服务

职责:
- 初始化认证相关的数据库表(UserTable)

注意: 数据库引擎和会话管理统一由 DBManagerService 负责
"""
from sqlalchemy import inspect, text

from pyspring.core.abstracts.interfaces.ISingleton import ISingletonService
from pyspring.core.services.system import SystemService
from pyspring.log.instance import logger
from pyspring.repositories.db.manager import DBManagerService
from pyspring.repositories.db.models.common.define import Base
from pyspring.security.core.config.loader import SecurityConfigManager


# 静态导入默认表


# ==================== 认证配置服务 ====================

class AuthConfigService(ISingletonService):
    """
    认证配置服务
    
    管理认证相关的配置和依赖
    """

    def __init__(self, db_manager: DBManagerService, system_service: SystemService, security_config: SecurityConfigManager):
        """
        初始化认证配置服务
        
        Args:
            db_manager: 数据库管理服务
            system_service: 系统服务
            security_config: 安全配置管理器
        """
        self.db_manager = db_manager
        self.system_service = system_service
        self.security_config = security_config

    async def init_tables(self) -> bool:
        """创建数据库表(如果表已存在且可用则跳过, 不存在则创建, 存在但不可用则抛异常)"""
        try:
            # 确保数据库服务已经初始化
            db_service = await self.db_manager.service()
            if db_service is None or self.db_manager.provider is None:
                logger.error("🚨 数据库服务未正确初始化")
                raise RuntimeError("数据库服务未正确初始化")

            engine = await self.db_manager.get_engine()

            # 检查表是否已存在
            async with engine.begin() as conn:
                # 检查所有需要的表是否存在

                def check_tables(sync_conn):
                    inspector = inspect(sync_conn)
                    existing = inspector.get_table_names()
                    required = [table.name for table in Base.metadata.sorted_tables]
                    return existing, required

                existing_tables, required_tables = await conn.run_sync(check_tables)

                # 如果所有表都存在
                if all(table in existing_tables for table in required_tables):
                    # 验证表结构是否可用(尝试简单查询)
                    try:
                        if required_tables:
                            # 动态获取一个表名进行验证，避免硬编码 'user'
                            check_table = required_tables[0]
                            result = await conn.execute(text(f"SELECT COUNT(*) FROM {check_table} LIMIT 1"))
                            result.fetchone()

                        logger.debug(f"✅ 认证表已存在且可用, 跳过创建: {', '.join(required_tables)}")
                        return True
                    except Exception as verify_error:
                        logger.error(f"🚨 认证表存在但不可用: {verify_error}")
                        raise RuntimeError(f"认证表存在但不可用, 可能结构损坏: {verify_error}")

                # 表不存在或部分表缺失, 创建所有表
                missing_tables = [t for t in required_tables if t not in existing_tables]
                if missing_tables:
                    logger.info(f"📝 检测到缺失的表: {', '.join(missing_tables)}, 开始创建...")

                await conn.run_sync(Base.metadata.create_all)
                logger.info(f"✅ 认证表创建成功: {', '.join(required_tables)}")

            return True
        except RuntimeError:
            # 重新抛出 RuntimeError(表结构问题)
            raise
        except Exception as e:
            logger.error(f"🚨 认证表创建失败: {e}")
            raise RuntimeError(f"无法创建认证表: {e}")
