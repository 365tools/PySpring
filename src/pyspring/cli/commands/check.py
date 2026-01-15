"""
PySpring Check Command
"""
from .check_ops.circular import run_check_circular
from .check_ops.encoding import run_check_encoding
from .check_ops.env import run as run_env_check
from .check_ops.imports import run_check_import
from .check_ops.lift import run_lift_imports
from .check_ops.references import run_check_references


def register_subcommand(subparsers):
    """Register check subcommands"""
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

    # Env check subcommand
    env_parser = check_subparsers.add_parser(
        'env',
        help='Check development environment',
        description='Diagnose Python environment, installation, and path issues'
    )
    env_parser.set_defaults(func=run_env_check)

    # Import check subcommand
    import_parser = check_subparsers.add_parser(
        'import',
        help='Check imports recursively in the project',
        description='Scan and verify imports for all Python files in the target directory'
    )
    import_parser.add_argument(
        'target',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    import_parser.add_argument(
        '--static',
        action='store_true',
        help='Use static analysis (AST) instead of importing modules. Can detect imports inside functions.'
    )
    import_parser.set_defaults(func=run_check_import)

    # Encoding check subcommand
    encoding_parser = check_subparsers.add_parser(
        'encoding',
        help='Check file encoding (utf-8 compliance)',
        description='Scan project files for encoding issues (non-utf-8 or BOM)'
    )
    encoding_parser.add_argument(
        'target',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    encoding_parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically fix encoding issues (convert to utf-8 without BOM)'
    )
    encoding_parser.set_defaults(func=run_check_encoding)

    # Lift imports subcommand (Refactoring)
    lift_parser = check_subparsers.add_parser(
        'lift-imports',
        help='Refactor: Lift local imports to top-level',
        description='Scan for local imports in functions and move them to top-level if safe (no circular dependencies). Adds comments if unsafe.'
    )
    lift_parser.add_argument(
        'target',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    lift_parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply changes (lift imports) to files. If not set, runs in dry-run mode.'
    )
    lift_parser.set_defaults(func=run_lift_imports)
    circular_parser = check_subparsers.add_parser(
        'circular',
        help='Check for circular dependencies',
        description='Scan project for circular imports using static analysis (AST)'
    )
    circular_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    circular_parser.set_defaults(func=run_check_circular)

    # References check subcommand
    ref_parser = check_subparsers.add_parser(
        'references',
        help='Check for unresolved references',
        description='Scan project for missing imports and undefined names'
    )
    ref_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    ref_parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to automatically fix missing imports for standard libraries'
    )
    ref_parser.set_defaults(func=run_check_references)
