"""
Cache cleanup operations
"""

import os
import shutil
from pathlib import Path

from pyspring.cli.core.ui.console import print_error, print_info, print_success


def clean_project_cache(verbose: bool = False):
    """
    Recursively clean project cache directories
    """
    root_dirs_to_clean = [".pyspring_cache", ".pytest_cache"]
    recursive_targets = {"__pycache__", ".pytest_cache"}

    cwd = Path.cwd()
    cleaned_count = 0

    # 1. Clean specific root dirs
    for target in root_dirs_to_clean:
        cache_dir = cwd / target
        if cache_dir.exists():
            try:
                if cache_dir.is_dir():
                    shutil.rmtree(cache_dir)
                else:
                    cache_dir.unlink()
                print_success(f"Cleaned root cache: {target}")
                cleaned_count += 1
            except Exception as e:
                print_error(f"Failed to clean {target}: {e}")

    # 2. Recursive Clean
    print_info("Scanning for recursive cache cleaning...")

    # Use os.walk for performance
    for root, dirs, files in os.walk(cwd):
        # Filter dirs in-place to recurse into them?
        # Actually we want to find recursive_targets and delete them.
        # If we delete a dir, we must remove it from 'dirs' so walk doesn't try to enter it.

        # Identify dirs to delete
        to_delete = [d for d in dirs if d in recursive_targets]

        for d in to_delete:
            full_path = Path(root) / d
            try:
                shutil.rmtree(full_path)
                if verbose:
                    print_success(f"Deleted: {full_path.relative_to(cwd)}")
                cleaned_count += 1
            except Exception as e:
                print_error(f"Failed to delete {d} in {root}: {e}")

            # Prevent walking into deleted dir
            dirs.remove(d)

    if cleaned_count == 0:
        print_info("No cache files found to clean.")
    else:
        print_success(f"Cleanup complete. Removed {cleaned_count} cache directories.")
