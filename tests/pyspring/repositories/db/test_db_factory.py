"""
数据库工厂功能测试
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from pyspring.repositories.db.factory import DBServiceFactory
from pyspring.repositories.db.config import DatabaseConfig, PostgreSQLConfig, SQLiteConfig, MySQLConfig, DatabasePoolConfig


class TestDBServiceFactory:
    """数据库服务工厂测试类"""
    
    def test_factory_initialization(self):
        """测试工厂初始化"""
        config = Mock(spec=DatabaseConfig)
        factory = DBServiceFactory(config)
        
        assert factory.config == config
        assert factory._service is None
        assert factory._service_type is None
        assert isinstance(factory._service_creators, dict)
        assert len(factory._service_creators) == 3  # sqlite, postgresql, mysql
    
    @pytest.mark.asyncio
    async def test_get_sqlite_service(self):
        """测试获取SQLite服务"""
        # 创建配置
        config = DatabaseConfig(type="sqlite")
        
        factory = DBServiceFactory(config)
        
        # 获取服务
        service = await factory.get_service()
        
        # 验证服务类型和单例特性
        assert service is not None
        assert factory._service_type == "sqlite"
        
        # 再次获取应返回相同实例（单例测试）
        service2 = await factory.get_service()
        assert service is service2
    
    @pytest.mark.asyncio
    async def test_get_postgresql_service(self):
        """测试获取PostgreSQL服务"""
        # 创建配置
        config = DatabaseConfig(
            type="postgresql",
            postgresql=PostgreSQLConfig(
                host="localhost",
                port=5432,
                database="test_db",
                user="test_user",
                password="test_pass"
            )
        )
        
        factory = DBServiceFactory(config)
        
        # 获取服务
        service = await factory.get_service()
        
        # 验证服务类型和单例特性
        assert service is not None
        assert factory._service_type == "postgresql"
        
        # 再次获取应返回相同实例（单例测试）
        service2 = await factory.get_service()
        assert service is service2
    
    @pytest.mark.asyncio
    async def test_get_mysql_service(self):
        """测试获取MySQL服务"""
        # 创建配置
        config = DatabaseConfig(
            type="mysql",
            mysql=MySQLConfig(
                host="localhost",
                port=3306,
                database="test_db",
                user="test_user",
                password="test_pass"
            )
        )
        
        factory = DBServiceFactory(config)
        
        # 获取服务
        service = await factory.get_service()
        
        # 验证服务类型和单例特性
        assert service is not None
        assert factory._service_type == "mysql"
        
        # 再次获取应返回相同实例（单例测试）
        service2 = await factory.get_service()
        assert service is service2
    
    @pytest.mark.asyncio
    async def test_unsupported_type_error(self):
        """测试不支持的类型抛出异常"""
        config = DatabaseConfig(type="unsupported_type")
        factory = DBServiceFactory(config)
        
        with pytest.raises(ValueError) as exc_info:
            await factory.get_service()
        
        assert "Unsupported database type" in str(exc_info.value)
        assert "sqlite, postgresql, mysql, auto" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_auto_mode_fallback(self):
        """测试auto模式降级功能"""
        # 使用mock来模拟连接失败场景
        config = DatabaseConfig(
            type="auto",
            postgresql=PostgreSQLConfig(host="", database="test", user="test"),
            mysql=MySQLConfig(host="localhost", port=3306, database="test", user="test"),
            sqlite=SQLiteConfig(database=":memory:")
        )
        
        factory = DBServiceFactory(config)
        
        # 在降级到sqlite的情况下获取服务
        service = await factory.get_service()
        
        # 验证最终使用了sqlite服务
        assert service is not None
        assert factory._service_type == "sqlite"
        
        # 验证单例特性
        service2 = await factory.get_service()
        assert service is service2