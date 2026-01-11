"""
调试 IoC 容器扫描过程
"""
import importlib
import pkgutil
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def debug_scan():
    """调试扫描过程"""
    print("=" * 60)
    print("🔍 调试 IoC 容器扫描过程")
    print("=" * 60)

    base_package = "pyspring.security"

    try:
        # 导入基础包
        package = importlib.import_module(base_package)
        print(f"\n✅ 成功导入基础包: {base_package}")
        print(f"   包路径: {package.__path__}")

        # 扫描所有子模块
        print(f"\n📦 扫描子模块:")
        modules_found = []
        for importer, modname, ispkg in pkgutil.walk_packages(
                path=package.__path__,
                prefix=package.__name__ + ".",
                onerror=lambda x: print(f"   ⚠️  错误: {x}")
        ):
            modules_found.append(modname)
            if 'initializer' in modname.lower():
                print(f"   ✨ {modname} {'(包)' if ispkg else '(模块)'}")

        print(f"\n总共找到 {len(modules_found)} 个模块")

        # 检查 initializer.py 是否被找到
        print(f"\n🎯 查找 initializer 模块:")
        auth_initializer_module = "pyspring.security.authentication.initializer"
        if auth_initializer_module in modules_found:
            print(f"   ✅ 找到: {auth_initializer_module}")

            # 尝试导入并检查类
            try:
                module = importlib.import_module(auth_initializer_module)
                print(f"   ✅ 成功导入模块")

                print(f"\n   模块中的类:")
                for name, obj in vars(module).items():
                    if isinstance(obj, type) and not name.startswith('_'):
                        print(f"      - {name} (模块: {obj.__module__})")
                        if name.endswith('Initializer'):
                            print(f"        ✨ 这是一个 Initializer 类!")
                            print(f"        obj.__module__ == modname: {obj.__module__ == auth_initializer_module}")
            except Exception as e:
                print(f"   ❌ 导入失败: {e}")
        else:
            print(f"   ❌ 未找到: {auth_initializer_module}")
            print(f"\n   找到的相关模块:")
            for mod in modules_found:
                if 'auth' in mod:
                    print(f"      - {mod}")

    except Exception as e:
        print(f"❌ 扫描失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    debug_scan()
