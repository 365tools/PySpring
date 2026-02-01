"""
测试IOC容器对构造函数默认值的处理

验证修复：当构造函数参数有默认值时，IoC容器应该使用该默认值，
而不是强行注入基本类型的默认值（如 bool -> False）
"""
import pytest
from pyspring.ioc.annotations.component import Component
from pyspring.ioc.annotations.scope import Singleton
from pyspring.ioc.context import ApplicationContext
from pyspring.ioc.lifecycle.initializer import IStartupInitializer


class TestDefaultValueHandling:
    """测试默认值处理"""

    def test_bool_parameter_with_default_true(self):
        """测试1: bool参数默认值为True时，应该保持True而不是被覆盖为False"""
        print("\n" + "=" * 80)
        print("测试: bool参数默认值处理")
        print("=" * 80)

        # 定义测试组件
        @Component
        @Singleton
        class TestInitializer(IStartupInitializer):
            def __init__(self, enabled: bool = True):
                super().__init__(enabled)
                self.test_enabled = enabled

            async def initialize(self) -> bool:
                return True

            def get_name(self) -> str:
                return "TestInitializer"

        # 创建容器并扫描
        context = ApplicationContext()
        context.scan(["__main__"])

        # 获取实例
        initializer = context.get_by_type(TestInitializer)

        # 验证enabled应该是True（构造函数默认值）
        print(f"✅ 获取到实例: {initializer}")
        print(f"   - enabled 属性: {initializer.enabled}")
        print(f"   - test_enabled 属性: {initializer.test_enabled}")
        
        assert initializer.enabled is True, f"Expected enabled=True, but got {initializer.enabled}"
        assert initializer.test_enabled is True, f"Expected test_enabled=True, but got {initializer.test_enabled}"
        
        print("✅ bool参数默认值处理 - 通过")

    def test_int_parameter_with_default_value(self):
        """测试2: int参数有默认值时，应该使用默认值"""
        print("\n" + "=" * 80)
        print("测试: int参数默认值处理")
        print("=" * 80)

        @Component
        class TestService:
            def __init__(self, timeout: int = 30, retries: int = 3):
                self.timeout = timeout
                self.retries = retries

        context = ApplicationContext()
        context.scan(["__main__"])

        service = context.get_by_type(TestService)
        
        print(f"✅ 获取到实例: {service}")
        print(f"   - timeout: {service.timeout}")
        print(f"   - retries: {service.retries}")
        
        assert service.timeout == 30, f"Expected timeout=30, but got {service.timeout}"
        assert service.retries == 3, f"Expected retries=3, but got {service.retries}"
        
        print("✅ int参数默认值处理 - 通过")

    def test_str_parameter_with_default_value(self):
        """测试3: str参数有默认值时，应该使用默认值"""
        print("\n" + "=" * 80)
        print("测试: str参数默认值处理")
        print("=" * 80)

        @Component
        class ConfigService:
            def __init__(self, env: str = "production", mode: str = "normal"):
                self.env = env
                self.mode = mode

        context = ApplicationContext()
        context.scan(["__main__"])

        service = context.get_by_type(ConfigService)
        
        print(f"✅ 获取到实例: {service}")
        print(f"   - env: {service.env}")
        print(f"   - mode: {service.mode}")
        
        assert service.env == "production", f"Expected env='production', but got {service.env}"
        assert service.mode == "normal", f"Expected mode='normal', but got {service.mode}"
        
        print("✅ str参数默认值处理 - 通过")

    def test_mixed_parameters_with_and_without_defaults(self):
        """测试4: 混合有默认值和无默认值的参数"""
        print("\n" + "=" * 80)
        print("测试: 混合参数默认值处理")
        print("=" * 80)

        @Component
        class DependencyService:
            def __init__(self):
                self.name = "DependencyService"

        @Component
        class MixedService:
            def __init__(self, dep: DependencyService, enabled: bool = True, count: int = 5):
                self.dep = dep
                self.enabled = enabled
                self.count = count

        context = ApplicationContext()
        context.scan(["__main__"])

        service = context.get_by_type(MixedService)
        
        print(f"✅ 获取到实例: {service}")
        print(f"   - dep: {service.dep}")
        print(f"   - enabled: {service.enabled}")
        print(f"   - count: {service.count}")
        
        assert service.dep is not None, "Dependency should be injected"
        assert isinstance(service.dep, DependencyService), "Dependency should be DependencyService"
        assert service.enabled is True, f"Expected enabled=True, but got {service.enabled}"
        assert service.count == 5, f"Expected count=5, but got {service.count}"
        
        print("✅ 混合参数默认值处理 - 通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
