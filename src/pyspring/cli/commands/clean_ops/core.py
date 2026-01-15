"""
Clean command core logic
"""
import sys
import traceback

from pyspring.cli.core.ui import print_title, print_error
from .cache import clean_project_cache


def run(args):
    """
    Execute clean command
    """
    print_title("Cleaning Project Cache")
    try:
        # Default behavior: clean pyspring cache
        clean_project_cache(verbose=args.verbose)

    except Exception as e:
        if args.verbose:
            traceback.print_exc()
        else:
            print_error(f"Error: {e}")
        sys.exit(1)
