"""
PySpring uv 命令核心逻辑
"""
import shutil
import subprocess
import sys
from pathlib import Path

from pyspring.cli.core.ui import print_section


def check_uv_installed():
    """检查 uv 是否已安装"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def setup_uv_env(dev_mode=True, rebuild=False):
    """
    配置 uv 环境
    1. 检查 uv
    2. 如果 rebuild=True，删除旧环境
    3. uv venv & uv pip install
    """
    print_section("Setting up uv environment")

    if not check_uv_installed():
        print("❌ uv is not installed. Please install uv first.")
        print("   pip install uv")
        sys.exit(1)

    venv_path = Path('.venv')
    if rebuild and venv_path.exists():
        print("Cleaning up old environment...")
        shutil.rmtree(venv_path, ignore_errors=True)

    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run(['uv', 'venv'], check=True)
    else:
        print("Virtual environment exists.")

    print("Installing dependencies...")
    cmd = ['uv', 'pip', 'install', '-e', '.']
    if dev_mode:
        # 尝试安装 dev 依赖 (uv pip install -e .[dev])
        # 如果 pyproject.toml 里没定义 dev，可能会报错，所以要检查一下
        # 简化处理：总是尝试安装
        cmd.append('[dev]')  # 假设项目遵循规范

    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Environment setup complete!")
    except subprocess.CalledProcessError:
        print("\n⚠️  Failed to install dependencies. Check pyproject.toml.")
        sys.exit(1)


def rebuild_uv_env():
    """完全重建环境"""
    setup_uv_env(rebuild=True)


def install_pyspring(dev_mode=False):
    """仅安装依赖"""
    print_section("Installing Dependencies")
    cmd = ['uv', 'pip', 'install', '-e', '.']
    if dev_mode:
        cmd[-1] = '.[dev]'

    subprocess.run(cmd)


def show_uv_status():
    """显示 uv 状态"""
    print_section("uv Environment Status")
    if Path('.venv').exists():
        print("✅ Virtual environment found (.venv)")
        # Show pip list
        print("\nInstalled Packages:")
        subprocess.run(['uv', 'pip', 'list'], check=False)
    else:
        print("❌ Virtual environment not found")


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
