"""
检查 AuthenticationInitializer 是否被误判为抽象类
"""
import inspect
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from pyspring.security.authentication.initializer import AuthenticationInitializer

print("=" * 60)
print("🔍 检查 AuthenticationInitializer")
print("=" * 60)

print(f"\n类名: {AuthenticationInitializer.__name__}")
print(f"模块: {AuthenticationInitializer.__module__}")
print(f"是否抽象类: {inspect.isabstract(AuthenticationInitializer)}")
print(f"基类: {[base.__name__ for base in AuthenticationInitializer.__bases__]}")

print(f"\n抽象方法:")
if hasattr(AuthenticationInitializer, '__abstractmethods__'):
    print(f"   {AuthenticationInitializer.__abstractmethods__}")
else:
    print(f"   (无)")

print(f"\n方法列表:")
for name in dir(AuthenticationInitializer):
    if not name.startswith('_') or name in ['__init__']:
        attr = getattr(AuthenticationInitializer, name)
        if callable(attr):
            print(f"   - {name}()")

print("\n" + "=" * 60)
