"""
Cache cleanup operations
"""
import shutil
from pathlib import Path


def clean_project_cache(verbose: bool = False):
    """
    Clean project cache directories
    """
    targets = [".pyspring_cache", ".pytest_cache"]

    for target in targets:
        cache_dir = Path(target)

        if verbose:
            print(f"Checking for cache at: {cache_dir.absolute()}")

        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"✅ Successfully cleaned cache directory: {target}")
            except Exception as e:
                print(f"❌ Failed to clean {target}: {e}")
        else:
            if verbose:
                print(f"ℹ️ Cache directory '{target}' not found. Nothing to clean.")
