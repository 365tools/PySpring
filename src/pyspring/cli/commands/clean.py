"""
PySpring Clean Command
"""
from .clean_ops.cache import clean_project_cache
from .clean_ops.imports import run_clean_imports


def register_subcommand(subparsers):
    """Register clean subcommands"""
    parser = subparsers.add_parser(
        'clean',
        help='Remove artifacts, caches, and unused code',
        description='Remove temporary files or clean unused codes'
    )

    clean_subparsers = parser.add_subparsers(
        title='Available Cleaners',
        dest='clean_command',
        required=True,
        metavar='<clean_command>'
    )

    # Cache cleaner
    cache_parser = clean_subparsers.add_parser(
        'cache',
        help='Clear system and framework caches',
        description='Remove project cache directories'
    )
    cache_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    cache_parser.set_defaults(func=lambda args: clean_project_cache(args.verbose))

    # Import cleaner
    import_parser = clean_subparsers.add_parser(
        'imports-unused',
        help='Remove detected unused import statements',
        description='Scanning and removing unused import statements'
    )
    import_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Path to clean (default: current directory)'
    )
    import_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    import_parser.set_defaults(func=run_clean_imports)
