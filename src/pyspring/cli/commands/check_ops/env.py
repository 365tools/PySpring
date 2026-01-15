"""
PySpring Environment Checker
"""
import os
import subprocess
import sys

import pyspring
from pyspring.cli.core.ui import print_section


def check_python_info():
    print_section("1. Python Environment Info")
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version: {sys.version}")
    print(f"Current Working Directory: {os.getcwd()}")

    # Check venv
    in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    print(f"In Virtual Environment: {'✅ Yes' if in_venv else '❌ No'}")
    if in_venv:
        print(f"Virtual Env Path: {sys.prefix}")


def check_pyspring_installation():
    print_section("2. PySpring Installation Check")

    # Use pip show
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "pyspring"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ PySpring is installed")
            for line in result.stdout.split('\n'):
                if any(key in line for key in ['Version:', 'Location:', 'Editable project location:']):
                    print(f"   {line}")
        else:
            print("❌ PySpring is NOT installed")
            print("\n💡 Please run: pip install pyspring")
            print("   Or for development: pip install -e /path/to/PySpring")
    except Exception as e:
        print(f"⚠️  Error checking installation: {e}")


def check_path_issues():
    print_section("3. Path Configuration Check")
    cwd = os.getcwd()
    sys_path = sys.path

    print(f"PYTHONPATH includes CWD: {'✅ Yes' if cwd in sys_path or '' in sys_path else '❌ No'}")

    # Check for src folder
    src_path = os.path.join(cwd, 'src')
    if os.path.exists(src_path):
        print(f"src directory found at: {src_path}")
        if src_path not in sys_path:
            print("⚠️  'src' directory exists but is NOT in sys.path. Imports might fail.")
        else:
            print("✅ 'src' directory is in sys.path")
    else:
        print("ℹ️  No 'src' directory found in current root.")


def check_import_ability():
    print_section("4. Import Check")
    try:
        print(f"✅ PySpring package is importable")
        print(f"   Location: {os.path.dirname(pyspring.__file__)}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import pyspring: {e}")
        print("   This usually means PySpring is installed but not accessible in current sys.path")
        return False


def suggest_solution():
    print("\n💡 Possible Solutions:")
    print("1. Ensure you have activated the correct virtual environment")
    print("   Run: .venv\\Scripts\\activate (Windows)")
    print("   Run: source .venv/bin/activate (Linux/Mac)")
    print("\n2. Ensure project root is in PYTHONPATH")
    print("   Run: $env:PYTHONPATH='path/to/project' (PowerShell)")
    print("   Run: export PYTHONPATH=$PYTHONPATH:/path/to/project (Bash)")
    print("\n3. If you are a developer, ensure you installed in edit mode")
    print("   Run: pip install -e .")
    print("\n4. Check your IDE interpreter settings")
    print("   Create a new .py file, type: from pyspring.log.instance import logger")
    print("   You should see code completion")


def run(args):
    """Run environment diagnosis"""
    print_section("PySpring Environment Diagnosis")

    check_python_info()
    check_pyspring_installation()
    check_path_issues()
    import_ok = check_import_ability()

    print_section("Diagnosis Result")

    # Check if in venv
    in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if import_ok:
        if not in_venv:
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
