"""
PySpring Check Command
"""
from .check_ops.encoding import run_check_encoding
from .check_ops.env import run as run_env_check
from .check_ops.imports import run_check_import


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
        default='src',
        help='Target directory to scan (default: src)'
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
        default='src',
        help='Target directory to scan (default: src)'
    )
    encoding_parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically fix encoding issues (convert to utf-8 without BOM)'
    )
    encoding_parser.set_defaults(func=run_check_encoding)
