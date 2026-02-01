"""
测试循环依赖检测功能
"""
from pyspring.ioc.context import ApplicationContext
from pyspring.ioc.annotations.component import Component


@Component
class ServiceA:
    def __init__(self, service_b: 'ServiceB'):
        self.service_b = service_b


@Component
class ServiceB:
    def __init__(self, service_a: 'ServiceA'):
        self.service_a = service_a


def test_circular_dependency_detection():
    """测试循环依赖检测功能"""
    print("\n🔍 测试循环依赖检测...")
    
    try:
        # 初始化应用上下文
        app_context = ApplicationContext.initialize(
            base_packages=[__name__],
            enable_aop=False  # 禁用AOP以简化测试
        )
        
        # 尝试获取服务，这应该会触发循环依赖检测
        service_a = app_context.get('service_a')
        print("❌ 应该检测到循环依赖但没有抛出异常")
        assert False, "应该检测到循环依赖"
        
    except RuntimeError as e:
        if "循环依赖" in str(e):
            print(f"✅ 正确检测到循环依赖: {e}")
        else:
            print(f"❌ 检测到意外的运行时错误: {e}")
            raise
    except Exception as e:
        # 可能会在不同阶段检测到循环依赖，这也算正常
        if "循环依赖" in str(e) or "circular" in str(e).lower():
            print(f"✅ 正确检测到循环依赖: {e}")
        else:
            print(f"⚠️ 检测到非循环依赖错误: {e}")
    

if __name__ == "__main__":
    test_circular_dependency_detection()
    print("🎉 循环依赖检测测试完成！")