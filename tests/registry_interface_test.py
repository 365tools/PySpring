"""
测试 ServiceRegistry 的接口类型检测功能
"""
from abc import ABC, abstractmethod
from typing import Protocol
from pyspring.ioc.context import ApplicationContext
from pyspring.ioc.annotations.component import Component


# 定义抽象基类
class AbstractService(ABC):
    @abstractmethod
    def do_work(self):
        pass


@Component
class ConcreteService(AbstractService):
    def do_work(self):
        return "Concrete service working"


# 定义协议
class ServiceProtocol(Protocol):
    def process(self) -> str:
        ...


@Component
class ProtocolImplementation:
    def process(self) -> str:
        return "Protocol implementation working"


def test_interface_registration():
    """测试接口类型注册功能"""
    print("\n🔍 测试接口类型注册...")
    
    # 初始化应用上下文
    app_context = ApplicationContext.initialize(
        base_packages=[__name__],
        enable_aop=False
    )
    
    # 测试抽象基类注册
    try:
        abstract_service = app_context.get_by_type(AbstractService)
        print(f"✅ 成功通过抽象类型获取服务: {type(abstract_service).__name__}")
    except ValueError as e:
        print(f"❌ 未能通过抽象类型获取服务: {e}")
    
    # 测试协议注册
    try:
        protocol_impl = app_context.get_by_type(ServiceProtocol)
        print(f"✅ 成功通过协议类型获取服务: {type(protocol_impl).__name__}")
    except ValueError as e:
        print(f"❌ 未能通过协议类型获取服务: {e}")
    
    # 测试具体类型注册
    concrete_service = app_context.get_by_type(ConcreteService)
    print(f"✅ 成功通过具体类型获取服务: {type(concrete_service).__name__}")
    
    print("🎉 接口类型注册测试完成！")


if __name__ == "__main__":
    test_interface_registration()