"""
测试 Resolver 改进：跳过有默认值的参数
"""
from typing import Type

import pytest
from pyspring.ioc.registry.registry import ServiceRegistry
from pyspring.ioc.resolver.resolver import DependencyResolver


class TestResolverSkipsDefaultParameters:
    """测试 Resolver 跳过有默认值的参数"""

    def test_skip_basic_type_with_default(self):
        """测试跳过基本类型的默认参数"""

        class ServiceWithBasicDefaults:
            def __init__(self, name: str = "default", count: int = 10, enabled: bool = True):
                self.name = name
                self.count = count
                self.enabled = enabled

        registry = ServiceRegistry()
        resolver = DependencyResolver(registry)

        # 分析依赖
        deps = resolver._analyze_dependencies(ServiceWithBasicDefaults)

        # 验证：所有有默认值的基本类型参数都应该被跳过
        assert len(deps) == 0, "有默认值的基本类型参数应该被跳过"

    def test_skip_type_parameter_with_default(self):
        """测试跳过 Type[...] 类型的默认参数"""

        class BaseModel:
            pass

        class ConcreteModel(BaseModel):
            pass

        class ServiceWithTypeDefaults:
            def __init__(
                    self,
                    model_type: Type[BaseModel] = ConcreteModel,
                    another_type: Type[str] = str
            ):
                self.model_type = model_type
                self.another_type = another_type

        registry = ServiceRegistry()
        resolver = DependencyResolver(registry)

        # 分析依赖
        deps = resolver._analyze_dependencies(ServiceWithTypeDefaults)

        # 验证：Type[...] 类型的默认参数应该被跳过
        assert len(deps) == 0, "Type[...] 类型的默认参数应该被跳过"

    def test_skip_complex_types_with_defaults(self):
        """测试跳过复杂类型的默认参数"""

        class ServiceWithComplexDefaults:
            def __init__(
                    self,
                    items: list = None,
                    config: dict = None,
                    callback=lambda x: x
            ):
                self.items = items or []
                self.config = config or {}
                self.callback = callback

        registry = ServiceRegistry()
        resolver = DependencyResolver(registry)

        # 分析依赖
        deps = resolver._analyze_dependencies(ServiceWithComplexDefaults)

        # 验证：所有有默认值的参数都应该被跳过
        assert len(deps) == 0, "有默认值的参数应该被跳过"

    def test_security_entity_configuration_example(self):
        """测试 SecurityEntityConfiguration 的实际场景"""
        from pyspring.repositories.db.models.common.define import BaseUserTable
        from pyspring.security.orm.tables import UserTable

        class MockSecurityConfig:
            def __init__(
                    self,
                    user_orm_model: Type[BaseUserTable] = UserTable,
                    enabled: bool = True,
                    name: str = "security"
            ):
                self.user_orm_model = user_orm_model
                self.enabled = enabled
                self.name = name

        registry = ServiceRegistry()
        resolver = DependencyResolver(registry)

        # 分析依赖
        deps = resolver._analyze_dependencies(MockSecurityConfig)

        # 验证：所有参数都有默认值，都应该被跳过
        assert len(deps) == 0, "所有有默认值的参数都应该被跳过"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
