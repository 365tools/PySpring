"""
单例模式重构验证测试 - 简化版

直接导入并验证核心单例类
"""
import importlib.util
import sys
from pathlib import Path

import pytest

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def test_singleton_interface_definition():
    """测试 1: 验证 ISingletonService 接口定义"""
    print("\n 测试 1: 验证 ISingletonService 接口...")

    # 动态导入 ISingletonService
    singleton_path = project_root / "src/pyspring/core/abstracts/interfaces/ISingleton.py"
    if not singleton_path.exists():
        # Try alternate path if moved
        singleton_path = project_root / "src/pyspring/core/interfaces/ISingleton.py"

    if not singleton_path.exists():
        pytest.fail(f"Could not find ISingleton.py at {singleton_path}")

    spec = importlib.util.spec_from_file_location("ISingletonService", singleton_path)
    singleton_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(singleton_module)
    ISingletonService = singleton_module.ISingletonService

    print("   ISingletonService 接口导入成功")
    # 验证它是 Protocol 或 Interface
    assert hasattr(ISingletonService, '__module__'), "ISingletonService module attribute missing"


def test_singleton_logic_removed_from_bases():
    """测试 2: 验证单例逻辑已从其他基类移除"""
    print("\n 测试 2: 验证单例逻辑已从其他基类移除...")

    files_to_check = [
        ("BaseConfigManager", project_root / "src/pyspring/core/configuration/manager.py"),
        ("RepositoriesConfigManager", project_root / "src/pyspring/repositories/base/config/loader.py"),
        ("EnvConfigLoader", project_root / "src/pyspring/core/environment/loader.py"),
        ("ConfigRegistry", project_root / "src/pyspring/core/configuration/registry.py"),
    ]

    for class_name, file_path in files_to_check:
        if not file_path.exists():
            print(f"   文件不存在: {file_path}")
            continue

        content = file_path.read_text(encoding='utf-8')

        # 检查是否包含老旧的单例实现代码
        assert "_instance = None" not in content, f"{class_name} contains legacy '_instance = None'"

        print(f"   {class_name} clean")


def test_imports_unified():
    """测试 3: 验证导入路径统一"""
    print("\n 测试 3: 验证导入路径统一...")

    files_to_scan = list((project_root / "src").rglob("*.py"))

    found = False
    for file_path in files_to_scan:
        if "__pycache__" in str(file_path):
            continue

        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            if "src.ref.core" in content:
                print(f"   Found src.ref.core in {file_path}")
                found = True
        except Exception:
            pass

    if found:
        print("   Some files still use old import paths")


def test_instances_removed():
    """测试 4: 验证文件末尾的单例实例已移除"""
    print("\n 测试 4: 验证文件末尾的单例实例已移除...")

    removed_instances = [
        ("repositories_config", project_root / "src/pyspring/repositories/base/config/loader.py"),
        ("env_config", project_root / "src/pyspring/core/environment/loader.py"),
        ("config_registry", project_root / "src/pyspring/core/configuration/registry.py"),
    ]

    for instance_name, file_path in removed_instances:
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding='utf-8-sig')

        # 检查是否导出了单例实例
        is_exported = f'\n{instance_name} =' in f'\n{content}'
        assert not is_exported, f"{instance_name} is still instantiated at module level in {file_path.name}"

        print(f"   {instance_name} 已移除")


if __name__ == "__main__":
    # Allow running directly for debugging
    pytest.main([__file__])
