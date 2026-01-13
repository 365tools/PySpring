"""
PySpring Import Checker

用于检测项目中的所有的导入状况，便于发现重构后的引用错误
"""
import importlib
import os
import sys
from typing import List, Tuple

from pyspring.cli.core.ui import print_section


def find_modules(base_path: str) -> List[str]:
    """
    Finds all Python modules in the given directory.
    Returns module names relative to the directory (assuming directory is in PYTHONPATH).
    """
    modules = []
    abs_base = os.path.abspath(base_path)

    if not os.path.exists(abs_base):
        return []

    ignored_dirs = {'.git', '.venv', 'venv', '__pycache__', 'build', 'dist', '.idea', '.vscode'}

    for root, dirs, files in os.walk(abs_base):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.endswith('.egg-info')]

        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                # Get full path
                full_path = os.path.join(root, file)
                # Get relative path
                rel_path = os.path.relpath(full_path, abs_base)

                # Convert to module notation
                if rel_path.startswith('..'):
                    continue

                module_path = os.path.splitext(rel_path)[0].replace(os.sep, '.')

                # Handle __init__
                if module_path.endswith('.__init__'):
                    module_path = module_path[:-9]

                # Skip top level __init__ if it results in empty string (package root)
                if not module_path:
                    pass

                modules.append(module_path)

    # Filter duplicates and sort
    return sorted(list(set(modules)))


def check_imports_list(modules: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
    success = []
    failed = []

    total = len(modules)
    print(f"\nChecking {total} modules...\n")

    for i, module_name in enumerate(modules, 1):
        if not module_name: continue

        try:
            # Try to import
            # We force reload if it's already loaded, to ensure we catch errors
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.import_module(module_name)

            success.append(module_name)
            print(f"[{i}/{total}] ✅ {module_name}")
        except Exception as e:
            failed.append((module_name, str(e)))
            print(f"[{i}/{total}] ❌ {module_name}")
            print(f"    Error: {e}")

    return success, failed


def register_subcommand(subparsers):
    """注册 check 子命令"""
    parser = subparsers.add_parser(
        'check',
        help='Check project health',
        description='Check project health and code integrity'
    )

    check_subparsers = parser.add_subparsers(
        title='Available Checks',
        dest='check_command',
        required=True,
        metavar='<check_command>'
    )

    # Import check subcommand
    import_parser = check_subparsers.add_parser(
        'import',
        help='Check imports recursively in the project',
        description='Scan and verify imports for all Python files in the target directory'
    )
    import_parser.add_argument(
        'target',
        nargs='?',
        default='src',
        help='Target directory to scan (default: src)'
    )
    import_parser.set_defaults(func=run_check_import)


def run_check_import(args):
    """运行导入检查命令"""
    target_dir = os.path.abspath(args.target)

    print_section(f"Checking imports in: {target_dir}")

    if not os.path.isdir(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist.")
        sys.exit(1)

    # Ensure target dir is in sys.path
    if target_dir not in sys.path:
        sys.path.insert(0, target_dir)
        print(f"Added {target_dir} to sys.path")

    # Also add current directory just in case
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    modules = find_modules(target_dir)

    if not modules:
        print("No modules found.")
        return

    success, failed = check_imports_list(modules)

    print("\n" + "=" * 50)
    print("Import Check Summary")
    print("=" * 50)
    print(f"Total Modules: {len(modules)}")
    print(f"Successful:    {len(success)}")
    print(f"Failed:        {len(failed)}")

    if failed:
        print("\nFailed Modules:")
        for name, error in failed:
            print(f" - {name}: {error}")
        sys.exit(1)
    else:
        print("\nAll modules imported successfully!")
