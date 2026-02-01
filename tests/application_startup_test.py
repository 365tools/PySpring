"""
PySpring 框架启动全流程测试

验证 PySpring 框架从初始化到启动再到关闭的完整生命周期
"""
import asyncio
from pyspring.ioc import ApplicationContext
from pyspring.ioc.annotations import Component, Singleton
from pyspring.log.instance import logger


# 测试组件
@Component
@Singleton
class TestService:
    """测试服务组件"""
    
    def __init__(self):
        self.initialized = False
        self.name = "TestService"
    
    def get_status(self):
        return f"{self.name} is running"


@Component
@Singleton
class AnotherTestService:
    """另一个测试服务，用于验证依赖注入"""
    
    def __init__(self, test_service: 'TestService'):
        self.test_service = test_service
        self.name = "AnotherTestService"
    
    def get_combined_status(self):
        return f"{self.name} -> {self.test_service.get_status()}"


async def test_application_lifecycle():
    """测试应用生命周期的完整流程"""
    print("\n" + "=" * 80)
    print("PySpring 框架启动全流程测试")
    print("=" * 80)
    
    # 模拟应用启动过程
    print("\n🔍 测试应用启动过程...")
    
    # 初始化应用上下文
    app_context = ApplicationContext.initialize(
        base_packages=[__name__],  # 扫描当前模块
        enable_aop=True
    )
    print("✅ ApplicationContext 初始化成功")
    
    # 初始化生命周期服务
    await app_context.container.initialize_lifecycle_services()
    print("✅ 生命周期服务初始化完成")
    
    # 测试服务注入和获取
    print("\n🔍 测试服务注入...")
    service = ApplicationContext.service(TestService)
    assert service is not None
    assert "TestService is running" in service.get_status()
    print("✅ 服务注入成功")
    
    # 测试依赖注入
    print("\n🔍 测试依赖注入...")
    another_service = ApplicationContext.service(AnotherTestService)
    assert another_service is not None
    expected_status = "AnotherTestService -> TestService is running"
    assert expected_status in another_service.get_combined_status()
    print("✅ 依赖注入成功")
    
    # 测试 get_by_type 方法
    print("\n🔍 测试 get_by_type 方法...")
    service_by_type = app_context.get_by_type(TestService)
    assert service_by_type is not None
    assert service_by_type.get_status() == "TestService is running"
    print("✅ get_by_type 方法工作正常")
    
    # 模拟应用关闭过程
    print("\n🔍 测试应用关闭过程...")
    await app_context.container.shutdown_lifecycle_services()
    print("✅ 生命周期服务关闭完成")
    
    # 重置应用上下文
    ApplicationContext.reset()
    print("✅ 应用上下文重置完成")
    
    print("\n" + "=" * 80)
    print("🎉 所有测试通过！PySpring 框架启动全流程验证成功")
    print("✅ 应用启动")
    print("✅ IoC 容器初始化") 
    print("✅ 服务注册与注入")
    print("✅ 依赖注入")
    print("✅ 应用关闭")
    print("=" * 80)


async def test_direct_context_operations():
    """测试直接上下文操作"""
    print("\n" + "=" * 60)
    print("直接上下文操作测试")
    print("=" * 60)
    
    # 直接初始化应用上下文
    app_context = ApplicationContext.initialize(
        base_packages=[__name__],
        enable_aop=True
    )
    
    print("✅ ApplicationContext 初始化成功")
    
    # 获取服务
    test_service = app_context.get_by_type(TestService)
    assert test_service is not None
    assert test_service.get_status() == "TestService is running"
    print("✅ 服务获取成功")
    
    # 验证依赖注入
    another_service = app_context.get_by_type(AnotherTestService)
    assert another_service is not None
    expected_status = "AnotherTestService -> TestService is running"
    assert another_service.get_combined_status() == expected_status
    print("✅ 依赖注入验证成功")
    
    # 测试 ApplicationContext.service 方法
    service_via_static = ApplicationContext.service(TestService)
    assert service_via_static is not None
    assert service_via_static.get_status() == "TestService is running"
    print("✅ ApplicationContext.service() 方法工作正常")
    
    # 清理
    ApplicationContext.reset()
    print("✅ 上下文重置成功")
    
    print("\n" + "=" * 60)
    print("🎉 直接上下文操作测试通过！")
    print("=" * 60)


async def test_lifecycle_services():
    """测试生命周期服务"""
    print("\n" + "=" * 60)
    print("生命周期服务测试")
    print("=" * 60)
    
    # 初始化应用上下文
    app_context = ApplicationContext.initialize(
        base_packages=[__name__],
        enable_aop=True
    )
    
    print("✅ ApplicationContext 初始化成功")
    
    # 初始化生命周期服务
    await app_context.container.initialize_lifecycle_services()
    print("✅ 生命周期服务初始化成功")
    
    # 验证服务正常工作
    service = app_context.get_by_type(TestService)
    assert service is not None
    print("✅ 服务在生命周期管理下正常工作")
    
    # 关闭生命周期服务
    await app_context.container.shutdown_lifecycle_services()
    print("✅ 生命周期服务关闭成功")
    
    # 重置上下文
    ApplicationContext.reset()
    print("✅ 上下文重置成功")
    
    print("\n" + "=" * 60)
    print("🎉 生命周期服务测试通过！")
    print("=" * 60)


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行 PySpring 框架启动全流程测试套件")
    
    # 运行所有异步测试
    await test_application_lifecycle()
    await test_direct_context_operations()
    await test_lifecycle_services()
    
    print("\n" + "=" * 80)
    print("🎉🎉🎉 所有测试通过！PySpring 框架完全可用！ 🎉🎉🎉")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_all_tests())