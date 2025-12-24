"""
PySpring 导入问题诊断脚本

在你的目标项目中运行此脚本来诊断问题
"""
import os
import subprocess
import sys


def print_section(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


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
    print_section("3. 导入测试")

    # 测试基础导入
    print("测试: import pyspring")
    try:
        import pyspring
        print(f"✅ 成功")
        print(f"   位置: {pyspring.__file__}")
    except ImportError as e:
        print(f"❌ 失败: {e}")
        return False

    # 测试具体模块
    modules = [
        ("pyspring.log.loguru.ins", "logger"),
        ("pyspring.ioc.manager", "AppContainerManager"),
    ]

    print("\n测试具体模块:")
    success = 0
    for module_name, attr_name in modules:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            getattr(module, attr_name)
            print(f"✅ {module_name}.{attr_name}")
            success += 1
        except Exception as e:
            print(f"❌ {module_name}.{attr_name}: {e}")

    return success == len(modules)


def check_sys_path():
    print_section("4. Python 搜索路径")
    print("前 10 个路径:")
    for i, path in enumerate(sys.path[:10], 1):
        print(f"   {i}. {path}")


def suggest_solution():
    print_section("5. 解决方案")

    in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        print("⚠️  你不在虚拟环境中！")
        print("\n🔴 这是导致 IDE 无法识别的主要原因！")
        print("\n📋 推荐步骤（解决 IDE 'Unresolved reference' 问题）:")
        print("\n1. 在项目目录创建虚拟环境:")
        print("   cd D:\\Project\\PycharmProjects\\FastAPIProject")
        print("   python -m venv venv")
        print("\n2. 激活虚拟环境:")
        print("   Windows PowerShell: venv\\Scripts\\Activate.ps1")
        print("   Windows CMD: venv\\Scripts\\activate.bat")
        print("   Linux/Mac: source venv/bin/activate")
        print("\n3. 在虚拟环境中安装 PySpring:")
        print("   pip install pyspring")
        print("   # 或开发模式: pip install -e D:\\Project\\PycharmProjects\\PySpring")
        print("\n4. 🔧 配置 IDE (重要！):")
        print("   ")
        print("   【VS Code】")
        print("   a) Ctrl+Shift+P → 'Python: Select Interpreter'")
        print("   b) 选择: .\\venv\\Scripts\\python.exe")
        print("   c) Ctrl+Shift+P → 'Python: Restart Language Server'")
        print("   d) Ctrl+Shift+P → 'Developer: Reload Window'")
        print("   ")
        print("   【PyCharm】")
        print("   a) File → Settings → Project → Python Interpreter")
        print("   b) Add Interpreter → Existing Environment")
        print("   c) 选择: D:\\Project\\PycharmProjects\\FastAPIProject\\venv\\Scripts\\python.exe")
        print("   d) File → Invalidate Caches / Restart → Invalidate and Restart")
    else:
        print("✅ 你在虚拟环境中")
        print("\n如果 IDE 仍显示 'Unresolved reference':")
        print("\n【VS Code】")
        print("1. 确认选择了正确的解释器:")
        print("   Ctrl+Shift+P → 'Python: Select Interpreter'")
        print("   应该显示虚拟环境的 Python")
        print("\n2. 重启语言服务器:")
        print("   Ctrl+Shift+P → 'Python: Restart Language Server'")
        print("\n3. 重新加载窗口:")
        print("   Ctrl+Shift+P → 'Developer: Reload Window'")
        print("\n【PyCharm】")
        print("1. 确认项目解释器:")
        print("   File → Settings → Project → Python Interpreter")
        print("   应该指向虚拟环境的 Python")
        print("\n2. 重建索引:")
        print("   File → Invalidate Caches / Restart")
        print("\n如果导入仍然失败，请运行:")
        print("   pip install pyspring")

    print("\n5. 验证:")
    print("   python -c \"from pyspring.log.loguru.ins import logger; print('✅ 成功!')\"")
    print("   pyspring diagnose")
    print("\n6. 在 IDE 中测试:")
    print("   创建新的 .py 文件，输入: from pyspring.log.loguru.ins import logger")
    print("   应该有代码提示和自动补全")


def main():
    print("=" * 70)
    print("PySpring 导入问题诊断")
    print("=" * 70)

    check_python_info()
    check_pyspring_installation()
    import_ok = check_import()
    check_sys_path()

    print_section("诊断结果")
    if import_ok:
        if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
            print("⚠️  PySpring 可以导入，但你不在虚拟环境中！")
            print("\n🔴 这会导致 IDE 无法识别 PySpring（显示 'Unresolved reference'）")
            print("\n💡 原因:")
            print("   - 命令行使用全局 Python（PySpring 已安装）")
            print("   - IDE 可能配置了不同的解释器或虚拟环境")
            print("   - IDE 无法找到全局安装的包")
            print("\n✅ 解决方法: 按照下方的 '5. 解决方案' 创建虚拟环境")
        else:
            print("🎉 PySpring 工作正常！可以开始使用了。")
            print("\n示例代码:")
            print("```python")
            print("from pyspring.log.loguru.ins import logger")
            print("from pyspring.ioc.manager import AppContainerManager")
            print("")
            print("logger.info('Hello PySpring!')")
            print("ioc = AppContainerManager()")
            print("```")
            print("\n💡 如果 IDE 仍显示 'Unresolved reference'，查看下方 '5. 解决方案'")
    else:
        print("❌ PySpring 导入失败")
        suggest_solution()

    print("\n" + "=" * 70)
    print("更多帮助: docs/INSTALLATION_OTHER_PROJECT.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
