"""
PySpring Check Command
"""
from .check_ops.circular import run_check_circular
from .check_ops.encoding import run_check_encoding
from .check_ops.env import run as run_env_check
from .check_ops.explicit import run_check_explicit_imports
from .check_ops.imports.validate import run_validate_imports
from .check_ops.lift import run_lift_imports
from .check_ops.refactor import run_check_refactor
from .check_ops.references import run_check_references
from ..core.formatter import SortedHelpFormatter


def register_subcommand(subparsers):
    """Register check subcommands"""
    parser = subparsers.add_parser(
        'check',
        help='Check project health',
        description='Check project health and code integrity',
        formatter_class=SortedHelpFormatter
    )

    check_subparsers = parser.add_subparsers(
        title='Available Checks',
        dest='check_command',
        required=True,
        metavar='<check_command>'
    )

    # 7. References check subcommand (Moved to top to test sorting)
    ref_parser = check_subparsers.add_parser(
        'references',
        help='Identify and fix unresolved symbol references',
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

    # 1. Encoding check subcommand
    encoding_parser = check_subparsers.add_parser(
        'encoding',
        help='Validate file encoding (UTF-8 compliance)',
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

    # 2. Env check subcommand
    env_parser = check_subparsers.add_parser(
        'env',
        help='Validate development environment and Python setup',
        description='Diagnose Python environment, installation, and path issues'
    )
    env_parser.set_defaults(func=run_env_check)

    # 3. Imports Circular check subcommand
    circular_parser = check_subparsers.add_parser(
        'imports-circular',
        help='Detect circular import dependencies',
        description='Scan project for circular imports using static analysis (AST)'
    )
    circular_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    circular_parser.set_defaults(func=run_check_circular)

    # 4. Explicit Imports Check (Expand imports to full path)
    explicit_parser = check_subparsers.add_parser(
        'imports-explicit',
        help='Refactor: Convert package imports to explicit submodules',
        description='Convert package-level imports (from pkg import Item) to submodule imports (from pkg.sub import Item) to bypass dynamic __init__ issues.'
    )
    explicit_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    explicit_parser.add_argument(
        '--fix',
        action='store_true',
        help='Apply changes modifying import statements'
    )
    explicit_parser.set_defaults(func=run_check_explicit_imports)

    # 8. Imports Refactor subcommand
    refactor_parser = check_subparsers.add_parser(
        'imports-refactor',
        help='Convert between absolute and relative imports',
        description='Refactor imports to be either absolute (default) or relative.'
    )
    refactor_parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Target directory (default: current directory)'
    )
    refactor_parser.add_argument(
        '--to-relative',
        action='store_true',
        help='Convert absolute imports to relative imports'
    )
    refactor_parser.add_argument(
        '--to-absolute',
        action='store_true',
        help='Convert relative imports to absolute imports (Default mode)'
    )
    refactor_parser.add_argument(
        '--level',
        type=int,
        default=2,
        metavar='',
        help='Max relative level allowed when converting to relative (default: 2)'
    )
    refactor_parser.add_argument(
        '--fix',
        action='store_true',
        help='Apply changes to files'
    )
    refactor_parser.set_defaults(func=run_check_refactor)

    # 5. Lift imports subcommand (Refactoring)
    lift_parser = check_subparsers.add_parser(
        'imports-lift',
        help='Refactor: Move local imports to module top-level',
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

    # 6. Imports Validation (Unified Check & Fix)
    validate_parser = check_subparsers.add_parser(
        'imports-validate',
        help='Validate imports and resolve missing modules',
        description='Comprehensive imports check. Detects missing modules (ModuleNotFoundError) and can auto-resolve broken paths.'
    )
    validate_parser.add_argument(
        'target',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    validate_parser.add_argument(
        '--mode',
        choices=['static', 'dynamic', 'all'],
        default='all',
        help='Check mode: all (default), static (AST-based, supports fix), or dynamic (Import-based)'
    )
    validate_parser.add_argument(
        '--fix',
        action='store_true',
        help='Auto-resolve broken imports by searching project index (only in static mode)'
    )
    validate_parser.add_argument(
        '--exclude',
        default='',
        metavar='',
        help='Comma-separated list of directories to exclude from scan'
    )
    validate_parser.set_defaults(func=run_validate_imports)
