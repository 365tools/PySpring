"""
集成测试：验证配置架构、IoC容器初始化、安全模块注册
"""
import pytest
from pyspring.ioc.context import ApplicationContext


class TestSecurityModuleIntegration:
    """测试安全模块集成"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每个测试前后清理容器"""
        # 清理之前的容器实例
        ApplicationContext._instance = None
        ApplicationContext._container = None
        yield
        # 清理测试后的容器
        ApplicationContext._instance = None
        ApplicationContext._container = None

    def test_security_entity_configuration_registered(self):
        """测试 SecurityEntityConfiguration 是否正确注册"""
        # 初始化容器（传入空包列表，框架包会自动加载）
        ApplicationContext.initialize(base_packages=['pyspring'])

        container = ApplicationContext.get_instance().container

        # 验证 SecurityEntityConfiguration 已注册
        from pyspring.security.authentication.config.entity import SecurityEntityConfiguration

        # 尝试通过类型获取服务（这是正确的方式）
        entity_config = container.get_by_type(SecurityEntityConfiguration)

        assert entity_config is not None, "SecurityEntityConfiguration 应该被注册"
        assert isinstance(entity_config, SecurityEntityConfiguration)

        # 验证配置包含必要的属性
        assert hasattr(entity_config, 'user_orm_model')
        assert hasattr(entity_config, 'role_orm_model')
        assert hasattr(entity_config, 'user_schema')

    def test_framework_packages_loaded_automatically(self):
        """测试框架包是否自动加载"""
        ApplicationContext.initialize(base_packages=['tests.integration'])

        container = ApplicationContext.get_instance().container
        all_names = container.registry.all_names()

        # 验证框架的核心服务已被加载
        security_services = [name for name in all_names if 'security' in name.lower()]
        assert len(security_services) > 0, "应该至少有一个安全相关的服务被注册"


class TestConfigurationIntegration:
    """测试配置集成"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """每个测试前后清理容器"""
        ApplicationContext._instance = None
        ApplicationContext._container = None
        yield
        ApplicationContext._instance = None
        ApplicationContext._container = None

    def test_config_manager_loaded(self):
        """测试 ConfigManager 是否正确加载"""
        from pyspring.config_manager import ConfigManager

        config = ConfigManager()

        # 测试加载各种配置
        logging_config = config.load_config('logging')
        assert logging_config is not None
        assert 'logging' in logging_config

        security_config = config.load_config('security')
        assert security_config is not None

        repositories_config = config.load_config('repositories')
        assert repositories_config is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
