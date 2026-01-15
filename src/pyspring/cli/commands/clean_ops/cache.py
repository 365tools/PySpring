"""
Cache cleanup operations
"""
import shutil
from pathlib import Path

from pyspring.cli.core.ui import print_info, print_success, print_error


def clean_project_cache(verbose: bool = False):
    """
    Clean project cache directories
    """
    targets = [".pyspring_cache", ".pytest_cache", "__pycache__"]

    for target in targets:
        cache_dir = Path(target)

        if verbose:
            print_info(f"Checking for cache at: {cache_dir.absolute()}")

        if cache_dir.exists():
            try:
                if cache_dir.is_dir():
                    shutil.rmtree(cache_dir)
                else:
                    cache_dir.unlink()
                print_success(f"Successfully cleaned cache directory: {target}")
            except Exception as e:
                print_error(f"Failed to clean {target}: {e}")
        else:
            if verbose:
                print_info(f"Cache directory '{target}' not found. Nothing to clean.")
