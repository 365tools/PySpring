"""
PySpring Environment Checker
"""
import os
import subprocess
import sys

import pyspring
from pyspring.cli.core.ui.console import (
    print_title, print_error, print_warning, print_info, Colors
)


def check_python_info():
    print_info("1. Python Environment Info")
    print(f"   Python Executable: {sys.executable}")
    print(f"   Python Version: {sys.version}")
    print(f"   Current Working Directory: {os.getcwd()}")

    # Check venv
    in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    print(f"   In Virtual Environment: {'[OK] Yes' if in_venv else '[X] No'}")
    if in_venv:
        print(f"   Virtual Env Path: {sys.prefix}")


def check_pyspring_installation():
    print_info("2. PySpring Installation Check")

    # Use pip show
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "pyspring"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("   [OK] PySpring is installed")
            output_lines = result.stdout.split('\n')
            is_editable = False
            for line in output_lines:
                if 'Editable project location:' in line:
                    is_editable = True
                    print(f"      {line}")
                elif any(key in line for key in ['Version:', 'Location:']):
                    print(f"      {line}")

            if not is_editable:
                print(f"      {Colors.OKCYAN}[i] Note: Runing in standard (copy) mode.{Colors.ENDC}")
                print(f"      {Colors.OKCYAN}  For local development, verify you installed with '-e' or 'editable=true'.{Colors.ENDC}")
        else:
            print("   [X] PySpring is NOT installed")
            print("\n      Tip: Please run: pip install pyspring")
            print("         Or for development: pip install -e /path/to/PySpring")
    except Exception as e:
        print_warning(f"Error checking installation: {e}")


def check_path_issues():
    print_info("3. Path Configuration Check")
    cwd = os.getcwd()
    sys_path = sys.path

    print(f"   PYTHONPATH includes CWD: {'[OK] Yes' if cwd in sys_path or '' in sys_path else '[X] No'}")

    # Check for src folder
    src_path = os.path.join(cwd, 'src')
    if os.path.exists(src_path):
        print(f"   src directory found at: {src_path}")
        if src_path not in sys_path:
            print_warning("'src' directory exists but is NOT in sys.path. Imports might fail.")
        else:
            print("   [OK] 'src' directory is in sys.path")
    else:
        print("   [i]  No 'src' directory found in current root.")


def check_import_ability():
    print_info("4. Import Check")
    try:
        # pyspring 是命名空间包，__file__ 为 None；用 __path__ 获取实际目录
        file_path: str | None = getattr(pyspring, "__file__", None)
        if file_path:
            location = os.path.dirname(file_path)
        else:
            path: list[str] | None = getattr(pyspring, "__path__", None)
            location = path[0] if path else None
        print(f"   [OK] PySpring package is importable")
        print(f"      Location: {location}")
        return True
    except Exception as e:
        print_error(f"Failed to import pyspring: {e}")
        print("      This usually means PySpring is installed but not accessible in current sys.path")
        return False


def suggest_solution():
    print("\nTip Possible Solutions:")
    print("1. Ensure you have activated the correct virtual environment")
    print("   Run: .venv\\Scripts\\activate (Windows)")
    print("   Or use uv: uv run pyspring check env")

    print("\n2. Ensure project dependencies are installed")
    print("   Run: uv sync")
    print("   Or:  pyspring uv install")

    print("\n3. If you are a developer, ensure you installed in edit mode")
    print("   Run: uv pip install -e .")

    print("\n4. Check your IDE interpreter settings")
    print("   Ensure it points to the .venv created by uv")


def run(args):
    """Run environment diagnosis"""
    print_title("PySpring Environment Diagnosis")

    check_python_info()
    print()  # spacer
    check_pyspring_installation()
    print()
    check_path_issues()
    print()
    checklist = []
    checklist.append(check_import_ability())

    if not all(checklist):
        suggest_solution()
        return False

    # Not using standard summary here as it's info-based, but could add footer
    print()
    return True
