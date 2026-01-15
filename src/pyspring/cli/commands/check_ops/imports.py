"""
PySpring Import Checker Command
"""
import importlib
import os
import sys
from typing import Generator

from pyspring.cli.component.files.ignore import get_ignore_list
from pyspring.cli.component.logging.filter import suppress_specific_logs
from pyspring.cli.core.ui import (
    print_title, print_file_header, print_issue, print_summary,
    print_error, print_info
)
from .static_import import run_ast_check


def find_modules_in_dir(scan_dir: str, root_dir: str) -> Generator[str, None, None]:
    """
    Find modules in a directory relative to a root (sys.path entry).
    scan_dir: absolute path to directory to scan
    root_dir: absolute path to a root in sys.path (e.g. project_root or src)
    """
    if not scan_dir.startswith(root_dir):
        return

    # Base package prefix
    rel = os.path.relpath(scan_dir, root_dir)
    if rel == '.':
        base_pkg = ''
    else:
        base_pkg = rel.replace(os.path.sep, '.') + '.'
        if base_pkg.startswith('.'): base_pkg = base_pkg[1:]

    ignored_dirs = get_ignore_list(os.getcwd())

    for root, dirs, files in os.walk(scan_dir):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.endswith('.egg-info')]

        if '__pycache__' in root:
            continue

        rel_path = os.path.relpath(root, scan_dir)

        if rel_path == '.':
            current_pkg_prefix = base_pkg
        else:
            current_pkg_prefix = base_pkg + rel_path.replace(os.path.sep, '.') + '.'

        for file in files:
            if file.endswith('.py') and file != '__init__.py':
                module_name = current_pkg_prefix + file[:-3]
                yield module_name
            elif file == '__init__.py':
                # yield package name (without trailing dot)
                pkg_name = current_pkg_prefix.rstrip('.')
                if pkg_name:
                    yield pkg_name


def run_check_import(args):
    """Run import check logic"""
    target_arg = getattr(args, 'target', '.')
    static_mode = getattr(args, 'static', False)

    target_path = os.path.abspath(target_arg)

    # Static Mode Delegate
    if static_mode:
        run_ast_check(target_path)
        return

    print_title(f"Dynamic Import Check: {target_arg}")

    project_root = os.getcwd()

    if not os.path.exists(target_path):
        print_error(f"Target path does not exist: {target_path}")
        sys.exit(1)

    # Setup sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    src_path = os.path.join(project_root, 'src')
    if os.path.exists(src_path) and src_path not in sys.path:
        sys.path.insert(0, src_path)

    # Determine the 'root' for import resolution
    import_root = project_root
    # Check if target path starts with src_path
    if os.path.exists(src_path) and target_path.startswith(src_path):
        import_root = src_path

    modules = list(find_modules_in_dir(target_path, import_root))

    if not modules:
        print_info("No Python modules found to check.")
        return

    total_modules = len(modules)
    failed_modules = []

    print_info(f"Found {total_modules} modules. Import testing...")

    # Use our context manager to suppress specific logs
    with suppress_specific_logs():
        for i, module_name in enumerate(modules, 1):
            try:
                importlib.import_module(module_name)
            except Exception as e:
                # Try to map module back to file for display
                try:
                    rel_path = module_name.replace('.', os.sep)
                    possible_path = os.path.join(import_root, rel_path + ".py")
                    if not os.path.exists(possible_path):
                        possible_path = os.path.join(import_root, rel_path, "__init__.py")

                    full_path = possible_path if os.path.exists(possible_path) else "Unknown file"
                except:
                    full_path = "Unknown file"

                failed_modules.append((module_name, str(e), full_path))

    # Reporting
    if failed_modules:
        for mod, err, path in failed_modules:
            print_file_header(path)
            print_issue("0", f"Import failed: {mod} -> {err}", path, level='error')

    print_summary(len(failed_modules), len(failed_modules), 0, fixable=False)

    if failed_modules:
        sys.exit(1)
