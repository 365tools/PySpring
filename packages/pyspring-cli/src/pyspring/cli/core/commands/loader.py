import importlib
import inspect
import logging
import pkgutil
import sys

from ..utils.logging import suppress_logs
from .base import BaseCommand


def load_commands(subparsers, package_path='pyspring.cli.commands'):
    """
    Dynamically loads command modules from the specified package path.
    Discovers and registers BaseCommand subclasses.

    Args:
        subparsers: The argparse subparsers object to register commands to.
        package_path: The dot-notation path to the commands package.
    """
    try:
        # Import the package to get its filesystem path
        package = importlib.import_module(package_path)
    except ImportError as e:
        logging.error(f"Failed to import commands package '{package_path}': {e}")
        return

    # Iterate through all modules in the package
    # Use suppress_logs to suppress expected noise from module-level initialization,
    # but capture the original stderr so genuine load errors are still visible.
    original_stderr = sys.stderr
    with suppress_logs(patterns=[r'.*']):
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
            # specific skip rules
            if name.startswith('_'):
                continue

            full_module_name = f"{package_path}.{name}"

            try:
                module = importlib.import_module(full_module_name)

                # Discover and register BaseCommand subclasses
                for _, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseCommand) and obj is not BaseCommand:
                        # Only register if the class is defined in this module
                        if obj.__module__ == module.__name__:
                            obj.register(subparsers)

            except Exception as e:
                # suppress_logs redirects sys.stderr; write to the ORIGINAL stderr so
                # command load failures are never silently swallowed.
                import traceback
                print(
                    f"\n[PySpring CLI] 警告：命令模块加载失败: {full_module_name}",
                    file=original_stderr,
                )
                print(f"[PySpring CLI] {type(e).__name__}: {e}", file=original_stderr)
                if __debug__:
                    traceback.print_exc(file=original_stderr)
                print("", file=original_stderr)
