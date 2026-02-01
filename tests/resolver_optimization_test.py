"""
测试 DependencyResolver 的优化功能
"""
from typing import List, Dict, Optional, Any
from pyspring.ioc.context import ApplicationContext
from pyspring.ioc.annotations.component import Component


@Component
class TestService:
    def __init__(self, 
                 name: str = "default", 
                 count: int = 0, 
                 enabled: bool = False,
                 data: List[str] = None,
                 mapping: Dict[str, int] = None,
                 optional_param: Optional[str] = None):
        self.name = name
        self.count = count
        self.enabled = enabled
        self.data = data or []
        self.mapping = mapping or {}
        self.optional_param = optional_param


def test_resolver_optimizations():
    """测试依赖解析器优化功能"""
    print("\n🔍 测试依赖解析器优化功能...")
    
    # 初始化应用上下文
    app_context = ApplicationContext.initialize(
        base_packages=[__name__],
        enable_aop=False
    )
    
    # 测试服务创建 - 应该能处理各种内置类型
    try:
        test_service = app_context.get_by_type(TestService)
        print(f"✅ 成功创建服务: {type(test_service).__name__}")
        print(f"  - name: {test_service.name!r}")
        print(f"  - count: {test_service.count}")
        print(f"  - enabled: {test_service.enabled}")
        print(f"  - data: {test_service.data}")
        print(f"  - mapping: {test_service.mapping}")
        print(f"  - optional_param: {test_service.optional_param}")
    except Exception as e:
        print(f"❌ 服务创建失败: {e}")
    
    print("🎉 依赖解析器优化测试完成！")


if __name__ == "__main__":
    test_resolver_optimizations()