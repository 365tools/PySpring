"""
PySpring uv 命令核心逻辑
"""
import shutil
import subprocess
import sys
from pathlib import Path

from pyspring.cli.core.ui import print_section


def get_locking_processes(path_str):
    """
    Get list of (pid, name) for processes locking the path (Windows only currently).
    Uses PowerShell to identify processes running executables within the target path.
    """
    if sys.platform != 'win32':
        return []

    # Ensure absolute path with backslashes for Windows
    target_path = str(Path(path_str).resolve())
    # Escape single quotes for PowerShell
    ps_target = target_path.replace("'", "''")

    # Command to find processes whose MainModule.FileName starts with the target path.
    # We filter by Path property of the process main module.
    cmd = [
        "powershell", "-NoProfile", "-Command",
        f"Get-Process | Where-Object {{ $_.Path -like '{ps_target}\\*' }} | Select-Object Id, ProcessName"
    ]

    try:
        # Create startupinfo to hide console window if possible (optional, but good for UI)
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if proc.returncode != 0:
            return []

        lines = proc.stdout.strip().splitlines()
        # Output format:
        #   Id ProcessName
        #   -- -----------
        #  796 python
        processes = []
        for line in lines:
            line = line.strip()
            # Skip header lines and empty lines
            if not line or line.startswith("Id") or line.startswith("--"):
                continue

            # Extract PID and Name
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                try:
                    pid = int(parts[0])
                    name = parts[1]
                    processes.append((pid, name))
                except ValueError:
                    pass
        return processes
    except Exception:
        return []


def kill_processes(pids):
    """Force kill processes by PID on Windows."""
    if sys.platform != 'win32' or not pids:
        return

    pid_str = ", ".join(str(p) for p in pids)
    cmd = ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid_str} -Force"]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def handle_locking_processes(venv_path):
    """
    Check for processes locking the venv folder and prompt to kill them.
    Returns:
        True: If no processes found or processes successfully killed.
        False: If user declined to kill processes or killing failed.
    """
    if sys.platform != 'win32':
        return True

    venv_abs = Path(venv_path).resolve()
    locking_procs = get_locking_processes(str(venv_abs))

    if not locking_procs:
        return True

    print(f"\n⚠️  Found {len(locking_procs)} background processes running from {venv_path}:")
    for pid, name in locking_procs:
        print(f"   - [PID: {pid}] {name}")

    print("\n   These processes prevent the environment from being rebuilt.")

    # Prompt user
    while True:
        answer = input("   Do you want to FORCE TERMINATE them and continue? (y/N): ").strip().lower()
        if answer in ('y', 'yes'):
            print("   Terminating processes...", end=" ", flush=True)
            pids = [p[0] for p in locking_procs]
            try:
                kill_processes(pids)
                print("Done.")
                return True
            except Exception as e:
                print(f"Failed: {e}")
                return False
        elif answer in ('n', 'no', ''):
            print("   Aborted.")
            return False


def check_windows_lock_issue():
    """
    Check if running on Windows inside the target venv.
    """
    if sys.platform != 'win32':
        return False

    # Check if sys.executable is inside the .venv directory of the current project
    # Assume .venv is in the current working directory
    venv_path = Path.cwd() / '.venv'
    if not venv_path.exists():
        return False

    try:
        exe_path = Path(sys.executable).resolve()
        venv_root = venv_path.resolve()
        # Check if venv path is a parent of the executable
        # e.g. D:\Project\.venv\Scripts\python.exe is inside D:\Project\.venv
        if venv_root in exe_path.parents:
            return True
    except Exception:
        pass
    return False


def check_uv_installed():
    """检查 uv 是否已安装"""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def print_activation_hint(venv_name='.venv'):
    """Print hints on how to activate the environment"""
    print_section("Next Steps")

    is_win = sys.platform == 'win32'
    activate_cmd = f".\\{venv_name}\\Scripts\\activate" if is_win else f"source {venv_name}/bin/activate"

    print("To activate the virtual environment, run:")
    print(f"  {activate_cmd}")
    print("\nOr run commands directly with 'uv run':")
    print("  uv run pyspring check")


def install_pyspring(dev_mode=False):
    """仅安装依赖"""
    # Windows 文件锁检查
    if check_windows_lock_issue():
        print("\n🛑 Windows File Lock Detected")
        print("   You are trying to update the package while running from its virtual environment.")
        print("   On Windows, this causes a 'PermissionError' because the executable is in use.")
        print("\n   Solution:")
        print("   1. Run 'deactivate' in your terminal.")
        print("   2. Run command again: 'uv sync' or 'pyspring uv install'")
        sys.exit(1)

    print_section("Installing Dependencies")

    # 优先使用 uv sync (如果 pyproject.toml 存在且配置了 tool.uv)
    if Path("pyproject.toml").exists() and "tool.uv" in Path("pyproject.toml").read_text(encoding="utf-8", errors='ignore'):
        cmd = ['uv', 'sync']
        if dev_mode:
            cmd.extend(['--extra', 'dev'])
    else:
        cmd = ['uv', 'pip', 'install', '-e', '.']
        if dev_mode:
            cmd[-1] = '.[dev]'

    subprocess.run(cmd)


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

    # Windows 文件锁检查 (如果正在重建，必须确保自己不在该环境中)
    if rebuild and check_windows_lock_issue():
        print("\n🛑 Windows File Lock Detected")
        print("   Cannot rebuild environment while running inside it.")
        print("   Please run 'deactivate' first.")
        sys.exit(1)

    venv_path = Path('.venv')
    if rebuild and venv_path.exists():
        # Check and handle background locking processes (e.g. orphan python.exe)
        if not handle_locking_processes(venv_path):
            sys.exit(1)

        print("Cleaning up old environment...")
        try:
            shutil.rmtree(venv_path)
        except OSError as e:
            print(f"Warning: Could not fully remove .venv ({e}).")
            print("Attempting to repair environment...")

    if rebuild or not venv_path.exists():
        print("Creating virtual environment...")
        # Use --allow-existing to support repair/overwrite if deletion failed
        subprocess.run(['uv', 'venv', '--allow-existing'], check=True)
    else:
        print("Virtual environment exists.")

    install_pyspring(dev_mode=dev_mode)

    print("\n✅ Environment setup complete!")
    print_activation_hint()


def rebuild_uv_env():
    """完全重建环境"""
    setup_uv_env(rebuild=True)


def show_uv_status():
    """显示 uv 状态"""
    print_section("uv Environment Status")
    venv_path = Path('.venv')
    if venv_path.exists():
        print(f"✅ Virtual environment found ({venv_path.absolute()})")

        # Check if active
        is_active = False
        try:
            if sys.executable.startswith(str(venv_path.absolute())):
                is_active = True
        except:
            pass

        if is_active:
            print("✅ Environment is currently ACTIVE")
        else:
            print("⚠️  Environment is NOT active in this terminal")
            print_activation_hint()

        # Show pip list summary
        print("\nInstalled Packages (Summary):")
        subprocess.run(['uv', 'pip', 'list'], check=False)
    else:
        print("❌ Virtual environment not found")
        print("\nTo create one, run:")
        print("  pyspring uv setup")


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
            print("\n✅ Install complete!")
            print_activation_hint()
        elif cmd == 'status':
            show_uv_status()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
