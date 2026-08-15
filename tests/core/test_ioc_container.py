"""
pyspring-core：IoC 容器测试

验证容器扫描、获取、按类型获取等核心能力。
Bean 注册通过扫描 @Component/@Service 装饰类完成。
"""
import pytest

from abc import ABC, abstractmethod

from pyspring.core.ioc.annotations.component import Component, Service
from pyspring.core.ioc.container.container import Container


# 被测组件定义在模块级，便于 scan 发现
@Component
class DemoComponent:
    """演示组件"""
    def hello(self) -> str:
        return "hello"


@Service
class DemoService:
    """演示服务"""
    def value(self) -> int:
        return 42


class IDemoInterface(ABC):
    """接口（抽象基类，用于 get_all_of_type 测试）"""

    @abstractmethod
    def run(self) -> str:
        """抽象方法"""
        ...


@Component
class DemoInterfaceImpl(IDemoInterface):
    """接口实现"""
    def run(self) -> str:
        return "impl"


class TestContainerBasics:
    """容器基础功能"""

    def test_scan_and_get_by_type(self):
        """测试扫描并通过类型获取 Bean"""
        container = Container()
        container.scan(['tests.core.test_ioc_container'])
        instance = container.get_by_type(DemoComponent)
        assert isinstance(instance, DemoComponent)
        assert instance.hello() == "hello"

    def test_service_scan(self):
        """测试 @Service 扫描"""
        container = Container()
        container.scan(['tests.core.test_ioc_container'])
        svc = container.get_by_type(DemoService)
        assert isinstance(svc, DemoService)
        assert svc.value() == 42

    def test_unknown_service_raises(self):
        """测试获取未注册服务抛异常"""
        container = Container()
        with pytest.raises(Exception):
            container.get('non_existent')

    def test_has_registered_bean(self):
        """测试 has 判断已注册 Bean"""
        container = Container()
        container.scan(['tests.core.test_ioc_container'])
        # Bean 名由 @Component 生成，为 demo_component（snake_case）
        assert container.has('demo_component')


class TestContainerScan:
    """容器扫描行为"""

    def test_component_is_registered(self):
        """测试 @Component 装饰的类被容器注册"""
        container = Container()
        container.scan(['tests.core.test_ioc_container'])
        assert container.has('demo_component')

    def test_scan_empty_package(self):
        """测试扫描空包不报错"""
        container = Container()
        container.scan([])
        assert not container.has('demo_component')


class TestContainerByType:
    """按类型获取"""

    def test_get_all_of_type(self):
        """测试按接口类型获取所有实现"""
        container = Container()
        container.scan(['tests.core.test_ioc_container'])
        results = container.get_all_of_type(IDemoInterface)
        assert any(isinstance(r, DemoInterfaceImpl) for r in results)

    def test_get_all_instances_of(self):
        """测试 get_all_instances_of 别名"""
        container = Container()
        container.scan(['tests.core.test_ioc_container'])
        results = container.get_all_instances_of(IDemoInterface)
        assert any(isinstance(r, DemoInterfaceImpl) for r in results)
