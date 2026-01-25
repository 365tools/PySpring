"""
模拟用户旧版 example 项目中的文件（没有 @Component 装饰器）
"""
from typing import Any

from pyspring.log.instance import logger


# 故意不添加 @Component 装饰器，模拟旧模板
class CustomPasswordLoginProvider:
    """
    自定义密码登录提供者 - 没有 @Component 装饰器
    """

    def __init__(self, user_provider, db, password_encoder):
        self.user_provider = user_provider
        self.db = db
        self.password_encoder = password_encoder
        logger.info("📦 创建自定义 CustomPasswordLoginProvider 实例")

    async def authenticate(self, request: Any) -> Any:
        """异步认证方法"""
        pass

    async def _find_user(self, identifier: str) -> Any:
        """异步查找用户"""
        pass


if __name__ == "__main__":
    import inspect
    import sys

    print("测试没有 @Component 装饰器的类...")

    try:
        # 模拟扫描器的操作
        module = sys.modules[__name__]

        print("\n1. inspect.getmembers(module, inspect.isclass):")
        members = inspect.getmembers(module, inspect.isclass)
        print(f"✅ 找到类: {[name for name, _ in members if not name.startswith('_')]}")

        for name, cls in members:
            if name == "CustomPasswordLoginProvider":
                print(f"\n2. 处理类: {name}")
                print(f"   __module__: {cls.__module__}")
                print(f"   有 __pyspring_component__: {hasattr(cls, '__pyspring_component__')}")

                print(f"\n3. inspect.getmembers(cls, inspect.isfunction):")
                try:
                    methods = inspect.getmembers(cls, inspect.isfunction)
                    print(f"✅ 找到方法: {[m for m, _ in methods]}")
                except Exception as e:
                    print(f"❌ 错误: {e}")
                    import traceback

                    traceback.print_exc()

    except Exception as e:
        print(f"❌ 整体错误: {e}")
        import traceback

        traceback.print_exc()
