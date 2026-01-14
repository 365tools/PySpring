"""
PySpring Clean Command
"""
from .clean_ops.core import run


def register_subcommand(subparsers):
    """Register clean subcommands"""
    parser = subparsers.add_parser(
        'clean',
        help='Clean project artifacts and caches',
        description='Remove temporary files like .pyspring_cache'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    parser.set_defaults(func=run)
