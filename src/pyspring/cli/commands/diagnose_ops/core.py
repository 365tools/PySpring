"""
PySpring 导入问题诊断脚本核心逻辑
"""
import os
import subprocess
import sys

from pyspring.cli.core.ui import print_section


def check_python_info():
    print_section("1. Python 环境信息")
    print(f"Python 可执行文件: {sys.executable}")
    print(f"Python 版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")

    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    print(f"是否在虚拟环境: {'✅ 是' if in_venv else '❌ 否'}")
    if in_venv:
        print(f"虚拟环境路径: {sys.prefix}")


def check_pyspring_installation():
    print_section("2. PySpring 安装检查")

    # 方法 1: 使用 pip show
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "pyspring"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ PySpring 已安装")
            for line in result.stdout.split('\n'):
                if any(key in line for key in ['Version:', 'Location:', 'Editable project location:']):
                    print(f"   {line}")
        else:
            print("❌ PySpring 未安装")
            print("\n💡 请运行: pip install pyspring")
            print("   或开发模式: pip install -e /path/to/PySpring")
    except Exception as e:
        print(f"⚠️  检查时出错: {e}")


def check_import():
    print_section("3. 动态导入检查")

    try:
        import pyspring
        print(f"✅ 成功导入 pyspring: {pyspring.__file__}")

        # 尝试检查版本
        try:
            from pyspring import __version__
            print(f"   版本: {__version__}")
        except ImportError:
            print("   ⚠️  无法获取 __version__")

        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 导入时发生异常: {e}")
        return False


def check_sys_path():
    print_section("4. sys.path 检查")
    for p in sys.path:
        print(f" - {p}")


def suggest_solution():
    print("\n💡 可能的解决方案:")
    print("1. 确保你激活了正确的虚拟环境")
    print("   Run: .venv\\Scripts\\activate (Windows)")
    print("   Run: source .venv/bin/activate (Linux/Mac)")
    print("\n2. 确保项目根目录在 PYTHONPATH 中")
    print("   Run: $env:PYTHONPATH='path/to/project' (PowerShell)")
    print("   Run: export PYTHONPATH=$PYTHONPATH:/path/to/project (Bash)")
    print("\n3. 如果你是开发者，确保使用了 -e 模式安装")
    print("   Run: pip install -e .")
    print("\n4. 检查你的 IDE 解释器设置")
    print("   创建新的 .py 文件，输入: from pyspring.log.instance import logger")
    print("   应该有代码提示和自动补全")


def run(args):
    """运行诊断命令"""
    print("=" * 70)
    print("PySpring Import Diagnosis")
    print("=" * 70)

    check_python_info()
    check_pyspring_installation()
    import_ok = check_import()
    check_sys_path()

    print_section("Diagnosis Result")
    if import_ok:
        if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
            print("⚠️  PySpring can be imported, but you are NOT in a virtual environment!")
            print("\n🔴 This may cause IDEs to fail recognizing PySpring (showing 'Unresolved reference')")
            print("\n💡 Reason:")
            print("   - CLI is using global Python (PySpring installed)")
            print("   - IDE might be using a different interpreter or venv")
            print("   - IDE might strictly enforce venv usage")
            print("\n✅ Solution: Create a virtual environment using 'pyspring uv setup'")
        else:
            print("🎉 PySpring is working correctly!")
            print("\nExample Code:")
            print("```python")
            print("from pyspring.log.instance import logger")
            print("from pyspring.ioc.manager import AppContainerManager")
            print("")
            print("logger.info('Hello PySpring!')")
            print("ioc = AppContainerManager()")
            print("```")
            print("\n💡 If IDE still shows 'Unresolved reference', check docs/TROUBLESHOOTING.md")
    else:
        print("❌ PySpring Import Failed")
        suggest_solution()

    print("\n" + "=" * 70)
    print("More Help: docs/INSTALLATION_OTHER_PROJECT.md")
    print("=" * 70)
