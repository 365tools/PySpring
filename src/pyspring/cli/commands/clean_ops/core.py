"""
Clean command core logic
"""
import sys

from .cache import clean_project_cache


def run(args):
    """
    Execute clean command
    """
    try:
        # Default behavior: clean pyspring cache
        clean_project_cache(verbose=args.verbose)

    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)
