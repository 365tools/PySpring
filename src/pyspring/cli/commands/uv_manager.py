"""
PySpring uv 命令 - 管理 uv 虚拟环境

提供便捷的 uv 虚拟环境管理命令
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

from pyspring.cli.core.ui import print_section


def check_uv_installed():
    """检查 uv 是否已安装"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def setup_uv_env(dev_mode=False, rebuild=False):
    """设置 uv 虚拟环境"""
    print_section("PySpring + uv 环境设置")

    # 检查 uv
    if not check_uv_installed():
        print("\n❌ 未找到 uv")
        print("\n安装 uv:")
        print("  Windows: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        print("  Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False

    print("\n✅ uv 已安装")

    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv and rebuild:
        print("\n⚠️  检测到当前在虚拟环境中")
        print("\n💡 请先退出虚拟环境，然后重新运行此命令")
        print("\n退出方法:")
        print("   deactivate")
        print("\n然后再执行:")
        print("   pyspring uv setup --rebuild")
        return False

    # 检查是否存在虚拟环境
    venv_path = Path('.venv')
    if venv_path.exists():
        if rebuild:
            print("\n🔄 重建虚拟环境...")
            print("   删除现有 .venv...")
            try:
                shutil.rmtree(venv_path)
                print("✅ 已删除")
            except PermissionError:
                print("❌ 删除失败，请关闭所有使用该环境的程序后重试")
                return False
            except Exception as e:
                print(f"❌ 删除失败: {e}")
                return False
        else:
            print("\n⚠️  虚拟环境已存在")
            print("💡 使用 --rebuild 参数重建: pyspring uv setup --rebuild")
            response = input("是否继续使用现有环境? (Y/n): ")
            if response.lower() == 'n':
                print("❌ 已取消")
                return False

    # 创建虚拟环境
    if not venv_path.exists():
        print("\n🏗️  创建虚拟环境...")
        result = subprocess.run(['uv', 'venv'], capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode != 0:
            print(f"❌ 创建失败: {result.stderr}")
            return False
        print("✅ 虚拟环境创建成功")

    # 安装 PySpring
    print("\n📦 安装 PySpring...")
    install_cmd = ['uv', 'pip', 'install']

    if dev_mode:
        print("   模式: 开发模式（可编辑）")
        # 尝试找到 PySpring 源码路径
        pyspring_paths = [
            r"D:\Project\PycharmProjects\PySpring",
            "../PySpring",
            "../../PySpring",
        ]
        pyspring_path = None
        for path in pyspring_paths:
            if Path(path).exists():
                pyspring_path = path
                break

        if pyspring_path:
            install_cmd.extend(['-e', pyspring_path])
        else:
            print("⚠️  未找到 PySpring 源码，改为标准安装")
            install_cmd.append('pyspring')
    else:
        print("   模式: 生产模式")
        install_cmd.append('pyspring')

    result = subprocess.run(install_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(f"❌ 安装失败")

        # 检查是否是 dependency-injector 编译问题
        stderr_text = result.stderr or ''

        # 检查是否是 pyspring.exe 被占用
        if 'pyspring.exe' in stderr_text and ('os error 32' in stderr_text or '另一个程序正在使用此文件' in stderr_text):
            print("\n⚠️  pyspring.exe 正在运行，无法更新")
            print("\n💡 解决方案:")
            print("\n方案1 - 退出虚拟环境后重试:")
            print("   1. 退出虚拟环境: deactivate")
            print("   2. 重新运行: pyspring uv setup --dev")

            print("\n方案2 - 使用全局 Python 运行:")
            print("   1. 退出虚拟环境: deactivate")
            print("   2. 使用全局命令: pyspring uv setup --dev")

            print("\n方案3 - 手动安装:")
            print("   1. 关闭所有使用 pyspring 的终端")
            if dev_mode and pyspring_path:
                print(f"   2. 运行: uv pip install -e {pyspring_path} --reinstall")
            else:
                print("   2. 运行: uv pip install pyspring --reinstall")

            return False

        if 'dependency-injector' in stderr_text or 'dependency_injector' in stderr_text:
            print("\n⚠️  dependency-injector 编译失败")
            print("\n💡 解决方案:")
            print("\n方案1 - 使用 pip 替代 uv（推荐）:")
            if dev_mode and pyspring_path:
                print(f"   激活环境后运行: pip install -e {pyspring_path}")
            else:
                print(f"   激活环境后运行: pip install pyspring")

            print("\n方案2 - 安装预编译版本:")
            if sys.platform == 'win32':
                print("   访问: https://www.lfd.uci.edu/~gohlke/pythonlibs/#dependency-injector")
                print("   下载并安装对应的 .whl 文件")

            print("\n后续步骤:")
            if sys.platform == 'win32':
                print("   1. 激活环境: .venv\\Scripts\\Activate.ps1")
            else:
                print("   1. 激活环境: source .venv/bin/activate")
            print(f"   2. 手动安装: pip install {'-e ' + pyspring_path if dev_mode and pyspring_path else 'pyspring'}")
        else:
            if stderr_text:
                print(f"\n错误详情:\n{stderr_text}")

        return False

    print("✅ PySpring 安装成功")

    # 总结
    print_section("✅ 设置完成")
    print("\n📋 后续步骤:")
    print("\n1. 激活虚拟环境:")
    if sys.platform == 'win32':
        print("   .venv\\Scripts\\Activate.ps1")
    else:
        print("   source .venv/bin/activate")

    print("\n2. 运行诊断:")
    print("   pyspring diagnose")

    print("\n3. 初始化项目:")
    print("   pyspring init")

    print("\n4. 在 IDE 中选择解释器:")
    if sys.platform == 'win32':
        print("   .\\.venv\\Scripts\\python.exe")
    else:
        print("   ./.venv/bin/python")

    return True


def rebuild_uv_env():
    """快速重建 uv 环境"""
    print_section("🔄 重建 uv 虚拟环境")

    # 检查是否在虚拟环境中
    in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print("\n⚠️  检测到当前在虚拟环境中")
        print("\n💡 请先退出虚拟环境，然后重新运行此命令")
        print("\n退出方法:")
        print("   deactivate")
        print("\n然后再执行:")
        print("   pyspring uv rebuild")
        print("\n为什么需要退出？")
        print("   - 重建需要删除 .venv 目录")
        print("   - 虚拟环境中的进程会锁定文件")
        print("   - 退出后才能安全删除和重建")
        return False

    venv_path = Path('.venv')

    # 删除现有环境
    if venv_path.exists():
        print("\n🗑️  删除现有 .venv...")

        # 尝试多种删除方法
        deleted = False

        # 方法1: 标准删除
        try:
            shutil.rmtree(venv_path)
            print("✅ 已删除")
            deleted = True
        except PermissionError:
            print("⚠️  文件被占用，尝试强制删除...")

            # 方法2: Windows rmdir 命令
            if sys.platform == 'win32':
                try:
                    result = subprocess.run(
                        ['cmd', '/c', 'rmdir', '/s', '/q', str(venv_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0 and not venv_path.exists():
                        print("✅ 已删除")
                        deleted = True
                except:
                    pass

            # 方法3: 重命名后删除
            if not deleted:
                try:
                    print("⚠️  尝试重命名方式...")
                    backup_path = Path(f'.venv.bak.{int(time.time())}')
                    venv_path.rename(backup_path)
                    print(f"✅ 已重命名为 {backup_path.name}")
                    print("💡 稍后可手动删除该目录")
                    deleted = True
                except:
                    pass

        if not deleted:
            print("\n❌ 无法删除 .venv 目录")
            print("\n💡 解决方法:")
            print("   1. 关闭所有使用该环境的 IDE 和终端")
            print("   2. 在 PowerShell 中运行:")
            print("      Get-Process | Where-Object {$_.Path -like '*\\.venv\\*'} | Stop-Process -Force")
            print("   3. 然后手动删除: Remove-Item .venv -Recurse -Force")
            print("   4. 再运行: pyspring uv rebuild")
            return False

        # 确保删除完成
        time.sleep(0.5)

    # 创建新环境
    print("\n🏗️  创建新虚拟环境...")
    result = subprocess.run(['uv', 'venv'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode != 0:
        print(f"❌ 创建失败: {result.stderr}")
        return False
    print("✅ 创建成功")

    # 安装 PySpring（开发模式）
    print("\n📦 安装 PySpring（开发模式）...")
    pyspring_paths = [
        r"D:\Project\PycharmProjects\PySpring",
        "../PySpring",
        "../../PySpring",
    ]

    pyspring_path = None
    for path in pyspring_paths:
        if Path(path).exists():
            pyspring_path = path
            break

    if pyspring_path:
        result = subprocess.run(
            ['uv', 'pip', 'install', '-e', pyspring_path],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
    else:
        result = subprocess.run(
            ['uv', 'pip', 'install', 'pyspring'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )

    if result.returncode != 0:
        print(f"❌ 安装失败")

        # 检查是否是 dependency-injector 编译问题
        stderr_text = result.stderr or ''

        # 检查是否是 pyspring.exe 被占用
        if 'pyspring.exe' in stderr_text and ('os error 32' in stderr_text or '另一个程序正在使用此文件' in stderr_text):
            print("\n⚠️  pyspring.exe 正在运行，无法更新")
            print("\n💡 解决方案:")
            print("   1. 退出当前终端")
            print("   2. 打开新终端，确保不在虚拟环境中")
            print("   3. 重新运行: pyspring uv rebuild")
            return False

        if 'dependency-injector' in stderr_text or 'dependency_injector' in stderr_text:
            print("\n⚠️  dependency-injector 编译失败")
            print("\n💡 解决方案:")
            print("\n方案1 - 安装预编译版本（推荐）:")
            if sys.platform == 'win32':
                print("   1. 访问: https://www.lfd.uci.edu/~gohlke/pythonlibs/#dependency-injector")
                print("   2. 下载对应 Python 版本的 .whl 文件")
                print("   3. 安装: uv pip install dependency_injector-4.42.0-*.whl")
            else:
                print("   安装开发工具: sudo apt-get install python3-dev build-essential")

            print("\n方案2 - 使用 pip 替代 uv:")
            print("   pip install -e " + (pyspring_path if pyspring_path else "pyspring"))

            print("\n方案3 - 跳过 PySpring 自动安装:")
            print("   1. 激活环境: .venv\\Scripts\\Activate.ps1")
            print("   2. 手动安装: pip install -e " + (pyspring_path if pyspring_path else "pyspring"))
        else:
            if stderr_text:
                print(f"\n错误详情:\n{stderr_text}")

        return False

    print("✅ 安装成功")
    print("\n🎉 环境重建完成！")

    print("\n📋 后续步骤:")
    if sys.platform == 'win32':
        print("1. 激活环境: .venv\\Scripts\\Activate.ps1")
    else:
        print("1. 激活环境: source .venv/bin/activate")
    print("2. 运行诊断: pyspring diagnose")

    return True


def show_uv_status():
    """显示 uv 环境状态"""
    print_section("uv 环境状态")

    # 检查 uv
    print("\n1. uv 安装状态:")
    if check_uv_installed():
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"   ✅ 已安装: {result.stdout.strip()}")
    else:
        print("   ❌ 未安装")
        print("   安装: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
        return

    # 检查虚拟环境
    print("\n2. 虚拟环境:")
    venv_path = Path('.venv')
    if venv_path.exists():
        print("   ✅ 存在: .venv/")

        # 检查 Python
        if sys.platform == 'win32':
            python_path = venv_path / 'Scripts' / 'python.exe'
        else:
            python_path = venv_path / 'bin' / 'python'

        if python_path.exists():
            result = subprocess.run([str(python_path), '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace')
            print(f"   Python: {result.stdout.strip()}")
    else:
        print("   ❌ 不存在")
        print("   创建: pyspring uv setup")

    # 检查 PySpring
    print("\n3. PySpring 安装:")
    try:
        result = subprocess.run(
            ['uv', 'pip', 'show', 'pyspring'],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5
        )
        if result.returncode == 0:
            print("   ✅ 已安装")
            for line in result.stdout.split('\n'):
                if any(key in line for key in ['Version:', 'Location:', 'Editable project location:']):
                    print(f"   {line}")
        else:
            print("   ❌ 未安装")
            print("   安装: pyspring uv install")
    except:
        print("   ⚠️  无法检查")


def install_pyspring(dev_mode=False):
    """安装 PySpring"""
    print_section("安装 PySpring")

    if not check_uv_installed():
        print("\n❌ 未找到 uv")
        return False

    if not Path('.venv').exists():
        print("\n❌ 虚拟环境不存在")
        print("💡 先创建环境: pyspring uv setup")
        return False

    print("\n📦 安装 PySpring...")

    if dev_mode:
        print("   模式: 开发模式")
        # 寻找源码
        pyspring_paths = [
            r"D:\Project\PycharmProjects\PySpring",
            "../PySpring",
            "../../PySpring",
        ]

        for path in pyspring_paths:
            if Path(path).exists():
                result = subprocess.run(
                    ['uv', 'pip', 'install', '-e', path],
                    capture_output=True, text=True, encoding='utf-8', errors='replace'
                )
                if result.returncode == 0:
                    print("✅ 安装成功")
                    return True
                else:
                    stderr_text = result.stderr or '编译错误'
                    print(f"❌ 安装失败: {stderr_text}")
                    return False

        print("⚠️  未找到源码，改为标准安装")

    # 标准安装
    result = subprocess.run(['uv', 'pip', 'install', 'pyspring'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if result.returncode == 0:
        print("✅ 安装成功")
        return True
    else:
        stderr_text = result.stderr or '编译错误'
        print(f"❌ 安装失败: {stderr_text}")
        return False


def print_help():
    """打印帮助信息"""
    print("""
PySpring uv 命令 - 管理 uv 虚拟环境

用法:
  pyspring uv <command> [options]

命令:
  setup        设置 uv 虚拟环境并安装 PySpring
  rebuild      快速重建虚拟环境
  install      在现有环境中安装 PySpring
  status       显示 uv 环境状态
  help         显示此帮助信息

选项:
  --dev        开发模式（可编辑安装）
  --rebuild    重建现有环境

示例:
  # 设置环境（生产模式）
  pyspring uv setup
  
  # 设置环境（开发模式）
  pyspring uv setup --dev
  
  # 重建环境
  pyspring uv rebuild
  
  # 查看状态
  pyspring uv status
  
  # 安装 PySpring
  pyspring uv install
  pyspring uv install --dev

提示:
  - 使用 uv 比 pip 快 10-100 倍
  - 虚拟环境创建在 .venv/ 目录
  - 开发模式会尝试查找 PySpring 源码并使用 -e 安装
  
常见问题:
  Q: dependency-injector 安装失败怎么办？
  A: 该包需要编译 C 扩展，uv 可能无法处理
     解决方法: 激活环境后使用 pip 手动安装
     .venv\\Scripts\\Activate.ps1
     pip install -e /path/to/PySpring
  
更多信息:
  https://github.com/365tools/PySpring
    """)


def register_subcommand(subparsers):
    """注册 uv 子命令"""
    parser = subparsers.add_parser(
        'uv',
        help='Manage uv virtual environment',
        description='Manage uv virtual environment lifecycle'
    )

    uv_subparsers = parser.add_subparsers(dest='uv_command', required=True, help='Sub-commands')

    # Setup
    setup_parser = uv_subparsers.add_parser('setup', help='Setup uv environment (create venv, install deps)')
    setup_parser.add_argument('--dev', action='store_true', help='Install development dependencies')
    setup_parser.add_argument('--rebuild', action='store_true', help='Recreate existing environment')

    # Rebuild
    uv_subparsers.add_parser('rebuild', help='Rebuild environment (clean and setup)')

    # Install
    install_parser = uv_subparsers.add_parser('install', help='Install PySpring dependencies')
    install_parser.add_argument('--dev', action='store_true', help='Install development dependencies')

    # Status
    uv_subparsers.add_parser('status', help='Show current environment status')

    parser.set_defaults(func=run)


def run(args):
    """运行 uv 命令"""
    cmd = args.uv_command

    try:
        if cmd == 'setup':
            setup_uv_env(dev_mode=args.dev, rebuild=args.rebuild)
        elif cmd == 'rebuild':
            rebuild_uv_env()
        elif cmd == 'install':
            install_pyspring(dev_mode=args.dev)
        elif cmd == 'status':
            show_uv_status()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def main():
    """Independent entry point"""
    import argparse
    parser = argparse.ArgumentParser(description='PySpring uv Manager')
    subparsers = parser.add_subparsers()
    register_subcommand(subparsers)

    # Allow running without explicit 'uv' subcommand when run directly
    # python uv_manager.py setup -> python uv_manager.py uv setup
    if len(sys.argv) > 1 and sys.argv[1] not in ['uv', '-h', '--help']:
        sys.argv.insert(1, 'uv')

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
