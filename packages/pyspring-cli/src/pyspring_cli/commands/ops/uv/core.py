"""
PySpring uv 命令核心逻辑
"""
import shutil
import subprocess
import sys
from pathlib import Path

from pyspring_cli.core.ui.console import print_section


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
    # Windows 文件锁检查 (跳过模式)
    try_skip_self = False
    
    if check_windows_lock_issue():
        print("\n\033[93m⚠ Windows File Lock Detected\033[0m")
        print("   You are running from the virtual environment you are trying to update.")
        print("   On Windows, updating the 'pyspring' package itself (editable mode) will fail.")

        # 尝试检测是否为 editable install
        # 如果是 editable install，我们其实不需要重新 pip install -e .，除非依赖变了
        # 但即便是依赖变了，uv sync 也会尝试更新当前包的 metadata，这可能会触发锁。

        # 策略改动：
        # 如果检测到锁，询问用户是否开启 "Safe Install" (不更新当前包本身，只安装依赖)

        print("\n   Automatic Switching to SAFE MODE:")
        print("   -> Will skip reinstalling 'pyspring' package itself to avoid PermissionError.")
        print("   -> Dependencies will still be installed/updated.")
        try_skip_self = True

    print_section("Installing Dependencies")

    # 优先使用 uv sync (如果 pyproject.toml 存在且配置了 tool.uv)
    if Path("pyproject.toml").exists() and "tool.uv" in Path("pyproject.toml").read_text(encoding="utf-8", errors='ignore'):
        # 只有在非锁模式下或者必须同步时才运行完整 sync，否则我们尝试用 pip install 安装依赖
        if not try_skip_self:
            cmd = ['uv', 'sync']
            if dev_mode:
                cmd.extend(['--extra', 'dev'])
            subprocess.run(cmd)
        else:
            # Safe Mode: 不运行 uv sync (因为它总是尝试操作当前项目环境)
            # 改为手动解析依赖并安装？或者使用 uv pip install --system (不推荐)

            # 更好的 Safe Mode 策略：
            # uv sync 实际上很难排除 root package。
            # 如果是 editable 模式，我们建议用户用 uv pip install 仅安装依赖
            print("   Executing: uv pip install requirements...")

            # 我们无法简单地从 pyproject.toml 提取所有依赖这里...
            # 妥协方案：尝试仅安装依赖而不安装 root
            # uv sync --no-install-project (如果 uv 支持，目前 uv sync 默认会安装 project)

            # 检查 uv 版本是否支持 --no-install-project (uv >= 0.4.0)
            # 假设用户用的是较新版本
            cmd = ['uv', 'sync', '--no-install-project']
            if dev_mode:
                cmd.extend(['--extra', 'dev'])

            # 尝试运行
            ret = subprocess.run(cmd)
            if ret.returncode != 0:
                print("\n\033[91m❌ 'uv sync --no-install-project' failed.\033[0m")
                print("   Your version of uv might be old or the configuration is invalid.")
                sys.exit(1)
            else:
                print("\n   ✅ Dependencies updated (project package skipped due to lock).")

    else:
        # 传统 pip 模式
        # cmd = ['uv', 'pip', 'install', '-e', '.']

        if try_skip_self:
            # 如果锁住了，就不能 install -e .
            # 只能尝试根据 pyproject.toml 安装依赖，比较麻烦
            print("   \033[93mSkipping pip install -e . due to file lock.\033[0m")
            print("   Please run 'deactivate' and retry if you need to update the project metadata.")
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


def inspect_module_in_venv(venv_path, module_name):
    """Inspect a module inside the virtual environment"""
    print(f"\n🔍 Inspecting module: {module_name}")

    python_exe = venv_path / 'Scripts' / 'python.exe' if sys.platform == 'win32' else venv_path / 'bin' / 'python'
    if not python_exe.exists():
        print("❌ Could not find python executable in .venv")
        return

    # Valid python script to run inside venv
    script = f"""
import sys
import os
import importlib.util
import importlib.metadata
import json
from pathlib import Path
from datetime import datetime

module_name = "{module_name}"
result = {{
    "name": module_name,
    "found": False,
    "version": None,
    "location": None,
    "editable": False,
    "direct_url": None,
    "updated": None
}}

try:
    try:
        dist = importlib.metadata.distribution(module_name)
        result["found"] = True
        result["version"] = dist.version
        
        durl = dist.read_text("direct_url.json")
        if durl:
            data = json.loads(durl)
            result["direct_url"] = data
            result["editable"] = data.get("dir_info", {{}}).get("editable", False)
            if "url" in data:
                 result["url"] = data["url"]
    except importlib.metadata.PackageNotFoundError:
        pass

    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
             result["found"] = True
             path_obj = Path(spec.origin)
             result["location"] = str(path_obj.parent)
             result["file"] = str(path_obj)
             try:
                 ts = path_obj.stat().st_mtime
                 result["updated"] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
             except:
                 pass
    except Exception:
        pass

except Exception as e:
    result["error"] = str(e)

print(json.dumps(result))
"""
    try:
        res = subprocess.run(
            [str(python_exe), "-c", script],
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            print("❌ Helper script failed")
            print(res.stderr)
            return

        import json
        try:
            data = json.loads(res.stdout.strip())
        except json.JSONDecodeError:
            print(f"❌ Failed to parse output: {res.stdout}")
            return

        if not data.get('found'):
            print(f"❌ Module '{module_name}' not found in environment.")
            return

        print(f"   Name:      {data['name']}")
        print(f"   Version:   {data['version'] or 'N/A'}")
        if data.get('updated'):
            print(f"   Updated:   {data['updated']}")

        print(f"   Location:  {data['location'] or 'N/A'}")
        if data.get('file'):
            print(f"   File:      {data['file']}")

        if data.get('editable'):
            print(f"   Mode:      ✅ EDITABLE")
            if data.get('url'):
                print(f"   Source:    {data['url']}")
        else:
            print(f"   Mode:      Standard")

    except Exception as e:
        print(f"❌ Error inspecting module: {e}")


def show_uv_status(module_name=None):
    """显示 uv 状态"""
    print_section("uv Environment Status")
    venv_path = Path('.venv')
    if venv_path.exists():
        print(f"✅ Virtual environment found ({venv_path.absolute()})")

        # Check if active
        is_active = False
        try:
            if sys.executable.lower().startswith(str(venv_path.absolute()).lower()):
                is_active = True
        except:
            pass

        if is_active:
            print("✅ Environment is currently ACTIVE")
        else:
            print("⚠️  Environment is NOT active in this terminal")

        if module_name:
            inspect_module_in_venv(venv_path, module_name)
        else:
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