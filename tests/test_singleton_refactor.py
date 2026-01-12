"""
单例模式重构验证测试

验证所有单例类都正确继承 ISingletonService 并可通过 IoC 容器管理
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_imports():
    """测试导入是否正确"""
    print("🔍 测试 1: 验证导入...")

    try:
        # 使用相对于 pyspring 的路径
        sys.path.insert(0, str(project_root / "src"))

        from src.pyspring.core.interfaces.ISingleton import ISingletonService
        print("  ✓ ISingletonService 导入成功")

        from src.pyspring.security.base.config.loader import SecurityConfigManager
        print("  ✓ SecurityConfigManager 导入成功")

        from src.pyspring.security.authentication.chain import AuthenticationChain
        print("  ✓ AuthenticationChain 导入成功")

        from src.pyspring.security.authentication.encryption import JWTEncryptionManager
        print("  ✓ JWTEncryptionManager 导入成功")

        from src.pyspring.log.loguru.config.manager import LoggingConfigManager
        print("  ✓ LoggingConfigManager 导入成功")

        from src.pyspring.repositories.base.config.loader import RepositoriesConfigManager
        print("  ✓ RepositoriesConfigManager 导入成功")

        from src.pyspring.core.config.manager import BaseConfigManager
        print("  ✓ BaseConfigManager 导入成功")

        from src.pyspring.core.config.registry import ConfigRegistry
        print("  ✓ ConfigRegistry 导入成功")

        from src.pyspring.core.env import EnvConfigLoader
        print("  ✓ EnvConfigLoader 导入成功")

        from src.pyspring.ioc.manager import AppContainerManager
        print("  ✓ AppContainerManager 导入成功")

        assert True
    except Exception as e:
        print(f"  ✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"导入失败: {e}"


def test_inheritance():
    """测试类是否正确继承 ISingletonService"""
    print("\n🔍 测试 2: 验证继承关系...")

    try:
        from src.pyspring.core.interfaces.ISingleton import ISingletonService
        from src.pyspring.security.base.config.loader import SecurityConfigManager
        from src.pyspring.security.authentication.chain import AuthenticationChain
        from src.pyspring.security.authentication.encryption import JWTEncryptionManager
        from src.pyspring.log.loguru.config.manager import LoggingConfigManager
        from src.pyspring.repositories.base.config.loader import RepositoriesConfigManager
        from src.pyspring.core.config.registry import ConfigRegistry
        from src.pyspring.core.env import EnvConfigLoader
        from src.pyspring.ioc.manager import AppContainerManager

        classes_to_test = [
            ("SecurityConfigManager", SecurityConfigManager),
            ("AuthenticationChain", AuthenticationChain),
            ("JWTEncryptionManager", JWTEncryptionManager),
            ("LoggingConfigManager", LoggingConfigManager),
            ("RepositoriesConfigManager", RepositoriesConfigManager),
            ("ConfigRegistry", ConfigRegistry),
            ("EnvConfigLoader", EnvConfigLoader),
            ("AppContainerManager", AppContainerManager),
        ]

        all_passed = True
        for name, cls in classes_to_test:
            if issubclass(cls, ISingletonService):
                print(f"  ✓ {name} 正确继承 ISingletonService")
            else:
                print(f"  ✗ {name} 未继承 ISingletonService")
                all_passed = False

        assert all_passed
    except Exception as e:
        print(f"  ✗ 继承测试失败: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"继承测试失败: {e}"


def test_no_custom_singleton():
    """测试类中是否移除了自定义单例逻辑"""
    print("\n🔍 测试 3: 验证移除自定义单例逻辑...")

    try:
        from src.pyspring.security.base.config.loader import SecurityConfigManager
        from src.pyspring.security.authentication.chain import AuthenticationChain
        from src.pyspring.security.authentication.encryption import JWTEncryptionManager

        classes_to_test = [
            ("SecurityConfigManager", SecurityConfigManager),
            ("AuthenticationChain", AuthenticationChain),
            ("JWTEncryptionManager", JWTEncryptionManager),
        ]

        all_passed = True
        for name, cls in classes_to_test:
            # 检查是否有 _instance 类属性
            if hasattr(cls, '_instance'):
                # 检查 _instance 是否是类级别的（不是实例级别的）
                if '_instance' in cls.__dict__:
                    print(f"  ⚠ {name} 仍有类级别 _instance 属性")
                    all_passed = False
                else:
                    print(f"  ✓ {name} 已移除类级别 _instance")
            else:
                print(f"  ✓ {name} 无 _instance 属性")

            # 检查是否重写了 __new__
            if '__new__' in cls.__dict__:
                print(f"  ⚠ {name} 仍重写了 __new__ 方法")
                all_passed = False
            else:
                print(f"  ✓ {name} 未重写 __new__")

        assert all_passed
    except Exception as e:
        print(f"  ✗ 单例逻辑检查失败: {e}")
        import traceback
        traceback.print_exc()
        assert False, f"单例逻辑检查失败: {e}"


def test_no_old_imports():
    """测试是否还有旧的 src.ref.core 导入"""
    print("\n🔍 测试 4: 验证导入路径统一...")

    import os

    old_imports_found = []

    # 递归搜索所有 Python 文件
    src_dir = project_root / "src" / "pyspring"
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if 'src.ref.core' in content:
                        # 找到具体的行
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if 'src.ref.core' in line:
                                rel_path = file_path.relative_to(project_root)
                                old_imports_found.append(f"{rel_path}:{i} - {line.strip()}")
                except Exception as e:
                    print(f"  ⚠ 无法读取文件 {file_path}: {e}")

    if old_imports_found:
        print(f"  ✗ 发现 {len(old_imports_found)} 处旧导入路径:")
        for imp in old_imports_found[:5]:  # 只显示前5个
            print(f"    - {imp}")
        if len(old_imports_found) > 5:
            print(f"    ... 还有 {len(old_imports_found) - 5} 处")
        assert False, f"发现 {len(old_imports_found)} 处旧导入路径"
    else:
        print("  ✓ 未发现旧导入路径 (src.ref.core)")
        assert True


def main():
    """运行所有测试"""
    print("=" * 70)
    print("PySpring 单例模式重构验证测试")
    print("=" * 70)

    results = {
        "导入测试": test_imports(),
        "继承关系测试": test_inheritance(),
        "单例逻辑移除测试": test_no_custom_singleton(),
        "导入路径统一测试": test_no_old_imports(),
    }

    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name:25s} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有测试通过！单例模式重构成功！")
    else:
        print("❌ 部分测试失败，请检查上述输出")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
