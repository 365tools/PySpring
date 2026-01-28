"""
测试扫描器处理异步函数的能力
"""
import inspect

from pyspring.ioc.annotations.component import Component


# 模拟 example 中的类结构
@Component
class TestAsyncClass:
    """测试异步方法的类"""

    def __init__(self):
        self.name = "test"

    async def async_method(self, param: str) -> str:
        """异步方法"""
        return param

    def sync_method(self, param: int) -> int:
        """同步方法"""
        return param * 2


if __name__ == "__main__":
    print("测试 inspect.getmembers() 处理异步方法...")

    try:
        # 测试 getmembers with isclass
        print("\n1. 测试 inspect.getmembers(module, inspect.isclass):")
        import sys

        module = sys.modules[__name__]
        members = inspect.getmembers(module, inspect.isclass)
        print(f"✅ 成功获取类成员: {[name for name, _ in members]}")

        # 测试 getmembers with isfunction
        print("\n2. 测试 inspect.getmembers(cls, inspect.isfunction):")
        for name, cls in members:
            if name == "TestAsyncClass":
                methods = inspect.getmembers(cls, inspect.isfunction)
                print(f"✅ 成功获取方法: {[name for name, _ in methods]}")

                for method_name, method in methods:
                    print(f"\n方法: {method_name}")
                    print(f"  类型: {type(method)}")
                    print(f"  是否协程函数: {inspect.iscoroutinefunction(method)}")
                    print(f"  __name__: {method.__name__}")
                    print(f"  __code__: {method.__code__}")

        # 测试 getmembers with ismethod (实例方法)
        print("\n3. 测试实例方法:")
        instance = TestAsyncClass()
        instance_methods = inspect.getmembers(instance, inspect.ismethod)
        print(f"✅ 成功获取实例方法: {[name for name, _ in instance_methods]}")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback

        traceback.print_exc()
