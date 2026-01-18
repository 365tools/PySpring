"""
PySpring Import Checker Command
"""
import importlib
import os
import sys
import warnings
from typing import Generator

from .....core.utils.filesystem import get_ignore_list, is_ignored
from .....core.utils.logging import suppress_logs

PYSPRING_LOG_PATTERNS = [
    r"✅ 已加载日志配置",
    r"⚙️ Loguru日志系统统配置完成",
    r"\[SecurityConfigManager\] 已加载配置文件"
]
from pyspring.cli.core.ui.console import (
    print_title, print_file_header, print_issue, print_summary,
    print_error, print_info, print_standard_import_tips
)


def find_modules_in_dir(scan_dir: str, root_dir: str, exclude_dirs: list = None) -> Generator[str, None, None]:
    """
    Find modules in a directory relative to a root (sys.path entry).
    scan_dir: absolute path to directory to scan
    root_dir: absolute path to a root in sys.path (e.g. project_root or src)
    exclude_dirs: list of specific directory names to exclude from scan
    """
    if not scan_dir.startswith(root_dir):
        return

    if exclude_dirs is None:
        exclude_dirs = []

    # Base package prefix
    rel = os.path.relpath(scan_dir, root_dir)
    if rel == '.':
        base_pkg = ''
    else:
        base_pkg = rel.replace(os.path.sep, '.') + '.'
        if base_pkg.startswith('.'): base_pkg = base_pkg[1:]

    ignored_dirs = get_ignore_list(os.getcwd())

    for root, dirs, files in os.walk(scan_dir):
        # Filter directories in-place using new logic
        dirs[:] = [d for d in dirs if not is_ignored(d, ignored_dirs) and d not in exclude_dirs]

        if is_ignored(os.path.basename(root), ignored_dirs):
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
    # static_mode = getattr(args, 'static', False) # Legacy argument

    target_path = os.path.abspath(target_arg)

    print_title(f"Dynamic Import Check: {target_path}")

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

    # Parse excluded directories
    user_exclude_str = getattr(args, 'exclude', '')
    user_excludes = [x.strip() for x in user_exclude_str.split(',') if x.strip()]

    modules = []

    # Special logic for projects with 'src' directory structure
    # If we are scanning the project root (default), we must scan 'src' separately
    # so that modules inside src are imported as 'package.foo' (root=src)
    # instead of 'src.package.foo' (root=project_root).
    is_root_scan = (target_path == project_root)

    if os.path.exists(src_path) and is_root_scan:
        # 1. Scan src folder with root=src_path
        modules.extend(find_modules_in_dir(src_path, src_path, exclude_dirs=user_excludes))
        # 2. Scan project root excluding src folder, with root=project_root
        exclude_dirs_for_root = user_excludes + ['src']
        modules.extend(find_modules_in_dir(project_root, project_root, exclude_dirs=exclude_dirs_for_root))
    else:
        # Determine the 'root' for import resolution
        import_root = project_root
        # Check if target path is inside src_path
        if os.path.exists(src_path) and (target_path.startswith(src_path + os.sep) or target_path == src_path):
            import_root = src_path

        modules = list(find_modules_in_dir(target_path, import_root, exclude_dirs=user_excludes))

    if not modules:
        print_info("No Python modules found to check.")
        return

    total_modules = len(modules)
    failed_modules = []

    print_info(f"Found {total_modules} modules. Import testing...")

    # Use our context manager to suppress specific logs
    # Also suppress warnings (like Pydantic V1 deprecation)
    with suppress_logs(PYSPRING_LOG_PATTERNS), warnings.catch_warnings():
        warnings.simplefilter("ignore")  # Ignore all warnings during scan
        
        for i, module_name in enumerate(modules, 1):
            try:
                importlib.import_module(module_name)
            except Exception as e:
                # Try to map module back to file for display
                try:
                    # Decide which root to use for path resolution
                    # When we built 'modules', we used either src_path or project_root
                    # If the module starts with a package found in src, try src_path first

                    search_roots = []
                    if os.path.exists(src_path):
                        search_roots.append(src_path)
                    search_roots.append(project_root)

                    full_path = "Unknown file"

                    rel_path = module_name.replace('.', os.sep)

                    for root in search_roots:
                        # Check module.py
                        candidate = os.path.join(root, rel_path + ".py")
                        if os.path.exists(candidate):
                            full_path = candidate
                            break
                        # Check package/__init__.py
                        candidate = os.path.join(root, rel_path, "__init__.py")
                        if os.path.exists(candidate):
                            full_path = candidate
                            break
                except:
                    full_path = "Unknown file"

                lineno = "0"
                if full_path != "Unknown file":
                    try:
                        tb = e.__traceback__
                        target_file = os.path.normcase(os.path.abspath(full_path))
                        while tb:
                            frame = tb.tb_frame
                            frame_file = os.path.normcase(os.path.abspath(frame.f_code.co_filename))
                            if frame_file == target_file:
                                lineno = str(tb.tb_lineno)
                            tb = tb.tb_next
                    except:
                        pass

                failed_modules.append((module_name, str(e), full_path, lineno))

    # Reporting
    if failed_modules:
        for mod, err, path, lineno in failed_modules:
            print_file_header(path)
            print_issue(lineno, f"Import failed: {mod} -> {err}", path, level='error')

    print_summary(len(failed_modules), len(failed_modules), 0, fixable=False)

    print_standard_import_tips(missing_imports=bool(failed_modules))

    if failed_modules:
        return False

    return True
