"""
PySpring Import Checker

用于检测项目中的所有的导入状况，便于发现重构后的引用错误
"""
import importlib
import os
import re
import sys
from contextlib import contextmanager
from typing import List, Tuple

from pyspring.cli.core.ui import print_section


class OutputFilter:
    """过滤标准输出流中的特定内容"""

    def __init__(self, original_stream, patterns):
        self.original_stream = original_stream
        self.patterns = [re.compile(p) for p in patterns]

    def write(self, data):
        # 如果数据包含匹配的模式，则跳过
        if any(p.search(data) for p in self.patterns):
            return
        self.original_stream.write(data)

    def flush(self):
        self.original_stream.flush()

    def __getattr__(self, name):
        return getattr(self.original_stream, name)


@contextmanager
def suppress_specific_logs():
    """拦截并抑制特定的日志输出"""
    # 需要拦截的日志模式
    patterns = [
        r"✅ 已加载日志配置",
        r"⚙️ Loguru日志系统统配置完成",
        r"\[SecurityConfigManager\] 已加载配置文件"  # 防止安全模块的输出
    ]

    # 替换标准流
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    sys.stdout = OutputFilter(original_stdout, patterns)
    sys.stderr = OutputFilter(original_stderr, patterns)

    # 尝试拦截 Loguru 的 sink
    try:
        from loguru import logger
        # 我们不能简单移除，因为那样会影响后续可能的合法使用（虽然 check 本身可能不需要）
        # 但 check 一般是静态的，我们这里选择移除所有 sink，只保留我们自己可控的（如果需要）
        logger.remove()

        # 添加一个过滤后的 sink，这样即使 Loguru 被重新配置，输出也会经过我们的 OutputFilter
        # 注意：如果 setup_logging_from_config 重新加载，它会添加新的 sink (stderr)
        # 所以 sys.stderr 的劫持是关键
    except ImportError:
        pass

    try:
        yield
    finally:
        # 恢复标准流
        sys.stdout = original_stdout
        sys.stderr = original_stderr


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

    # 使用上下文管理器抑制日志
    with suppress_specific_logs():
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
