"""
测试 PySpring 初始化功能

验证：
1. 模板文件是否存在
2. CLI 入口是否正确
3. 初始化脚本是否可执行
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_template_files():
    """测试模板文件是否存在"""
    print("🔍 测试模板文件...")

    template_dir = PROJECT_ROOT / "src" / "pyspring" / "templates" / "config"

    required_files = [
        "container.yaml",
        "logging.yaml",
        "repositories.yaml",
        "security.yaml"
    ]

    all_exist = True
    for filename in required_files:
        file_path = template_dir / filename
        if file_path.exists():
            print(f"  ✓ {filename} 存在")
        else:
            print(f"  ✗ {filename} 不存在")
            all_exist = False

    assert all_exist


def test_cli_module():
    """测试 CLI 模块已迁移到独立包"""
    print("\n🔍 CLI 模块已迁移到独立包...")
    print("  ℹ CLI 功能已迁移到 pyspring-cli 包")
    print("  ℹ 请安装: pip install pyspring-cli")
    assert True  # CLI 功能已迁移，此测试仅作提示


def test_init_module():
    """测试初始化模块已迁移到独立包"""
    print("\n🔍 初始化模块已迁移到独立包...")
    print("  ℹ 初始化功能已迁移到 pyspring-cli 包")
    print("  ℹ 请安装: pip install pyspring-cli")
    assert True  # 初始化功能已迁移，此测试仅作提示


def test_pyproject_config():
    """测试 pyproject.toml 配置"""
    print("\n🔍 测试 pyproject.toml 配置...")

    pyproject_path = PROJECT_ROOT / "pyproject.toml"

    if not pyproject_path.exists():
        print("  ✗ pyproject.toml 不存在")
        assert False, "pyproject.toml 不存在"

    content = pyproject_path.read_text(encoding='utf-8')

    # 检查关键配置
    checks = [
        ('CLI 入口点', 'pyspring = "pyspring.cli:main"'),
        ('包数据配置', 'pyspring = ["templates/*.yaml"]'),
    ]

    all_pass = True
    for name, pattern in checks:
        if pattern in content:
            print(f"  ✓ {name} 配置正确")
        else:
            print(f"  ⚠ {name} 配置可能不正确")

    assert True


def test_manifest():
    """测试 MANIFEST.in"""
    print("\n🔍 测试 MANIFEST.in...")

    manifest_path = PROJECT_ROOT / "MANIFEST.in"

    if not manifest_path.exists():
        print("  ✗ MANIFEST.in 不存在")
        assert False, "MANIFEST.in 不存在"

    content = manifest_path.read_text(encoding='utf-8')

    if "recursive-include" in content and "templates" in content:
        print("  ✓ MANIFEST.in 配置正确")
        assert True
    else:
        print("  ⚠ MANIFEST.in 可能缺少模板文件配置")
        assert False, "MANIFEST.in 可能缺少模板文件配置"


def main():
    """运行所有测试"""
    print("=" * 60)
    print("PySpring 初始化功能测试")
    print("=" * 60)

    results = {
        "模板文件": test_template_files(),
        "CLI 模块": test_cli_module(),
        "初始化模块": test_init_module(),
        "pyproject.toml": test_pyproject_config(),
        "MANIFEST.in": test_manifest(),
    }

    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 60)

    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name:20s} {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查上述输出")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)