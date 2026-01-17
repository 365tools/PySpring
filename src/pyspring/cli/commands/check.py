"""
PySpring Check Command
"""
from pyspring.cli.core.ui import print_title, print_success, print_error, print_warning
from .ops.check.circular import run_check_circular
from .ops.check.encoding import run_check_encoding
from .ops.check.env import run as run_env_check
from .ops.check.explicit import run_check_explicit_imports
from .ops.check.imports.validate import run_validate_imports
from .ops.check.lift import run_lift_imports
from .ops.check.refactor import run_check_refactor
from .ops.check.references import run_check_references

from ..core.arg_parser import print_friendly_subcommand_help
from ..core.formatter import SortedHelpFormatter

# Registry for automatic execution via --all
CHECK_REGISTRY = {
    'encoding': run_check_encoding,
    'env': run_env_check,
    'imports-circular': run_check_circular,
    'imports-explicit': run_check_explicit_imports,
    'imports-lift': run_lift_imports,
    'imports-refactor': run_check_refactor,
    'imports-validate': run_validate_imports,
    'references': run_check_references,
}

# Shared descriptions for CLI help and summary
CHECK_DESCRIPTIONS = {
    'encoding': 'Validate file encoding (UTF-8 compliance)',
    'env': 'Validate development environment and Python setup',
    'imports-circular': 'Detect circular import dependencies',
    'imports-explicit': 'Refactor: Convert package imports to explicit submodules',
    'imports-lift': 'Refactor: Move local imports to module top-level',
    'imports-refactor': 'Convert between absolute and relative imports',
    'imports-validate': 'Validate imports and resolve missing modules',
    'references': 'Identify and fix unresolved symbol references',
}


class CheckArgs:
    """Mock arguments for running checks programmatically"""

    def __init__(self):
        self.path = '.'
        self.target = '.'
        self.fix = False
        self.mode = 'all'
        self.exclude = ''
        self.to_relative = False
        self.to_absolute = False
        self.level = 2
        self.all = True
        self.apply = False


def run_all_checks(args, subparsers_action=None):
    """Execution logic for check --all"""
    if not args.all:
        if getattr(args, 'check_command', None) is None:
            if subparsers_action:
                print_friendly_subcommand_help(subparsers_action, prog_name='pyspring')
            return

    print_title("PySpring Health Diagnosis (All Checks)")

    results = []
    sorted_keys = sorted(CHECK_REGISTRY.keys())

    for name in sorted_keys:
        func = CHECK_REGISTRY[name]
        print(f"\n>> Running Check: {name}...")
        try:
            mock_args = CheckArgs()
            result = func(mock_args)
            results.append((name, result))
        except Exception as e:
            print_error(f"Check '{name}' crashed: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("CHECK SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ ISSUES"
        if not success: all_passed = False
        print(f"{name:<20} : {status}")

    print("-" * 60)

    if all_passed:
        print_success("All checks passed! Project is healthy.")
    else:
        print_warning("Some checks found issues.")

        fixable_commands = {
            'encoding', 'imports-explicit', 'imports-lift',
            'imports-refactor', 'imports-validate', 'references'
        }

        print("\n[Action Required]")
        for name, success in results:
            if not success:
                print(f"\n  • {name} found issues:")
                print(f"      Check: pyspring check {name}")
                if name in fixable_commands:
                    print(f"      Fix:   pyspring check {name} --fix")
                else:
                    print(f"      Fix:   Manual resolution required")

    # Add final separator for clean UI
    print()
    print("-" * 60)



def register_subcommand(subparsers):
    """Register check subcommands"""
    parser = subparsers.add_parser(
        'check',
        help='Check project health',
        description='Check project health and code integrity',
        formatter_class=SortedHelpFormatter
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all available checks in sequence and report summary'
    )
    
    check_subparsers = parser.add_subparsers(
        title='Available Checks',
        dest='check_command',
        required=False,
        metavar='<check_command>'
    )

    # Store the subparser action in a lambda default
    parser.set_defaults(func=lambda args: run_all_checks(args, check_subparsers))

    # 7. References check subcommand (Moved to top to test sorting)
    ref_parser = check_subparsers.add_parser(
        'references',
        help=CHECK_DESCRIPTIONS['references'],
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
        help=CHECK_DESCRIPTIONS['encoding'],
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
        help=CHECK_DESCRIPTIONS['env'],
        description='Diagnose Python environment, installation, and path issues'
    )
    env_parser.set_defaults(func=run_env_check)

    # 3. Imports Circular check subcommand
    circular_parser = check_subparsers.add_parser(
        'imports-circular',
        help=CHECK_DESCRIPTIONS['imports-circular'],
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
        help=CHECK_DESCRIPTIONS['imports-explicit'],
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
        help=CHECK_DESCRIPTIONS['imports-refactor'],
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
        help=CHECK_DESCRIPTIONS['imports-lift'],
        description='Scan for local imports in functions and move them to top-level if safe (no circular dependencies). Adds comments if unsafe.'
    )
    lift_parser.add_argument(
        'target',
        nargs='?',
        default='.',
        help='Target directory to scan (default: current directory)'
    )
    lift_parser.add_argument(
        '--fix',
        action='store_true',
        help='Apply changes (lift imports) to files. If not set, runs in dry-run mode.'
    )
    lift_parser.set_defaults(func=run_lift_imports)

    # 6. Imports Validation (Unified Check & Fix)
    validate_parser = check_subparsers.add_parser(
        'imports-validate',
        help=CHECK_DESCRIPTIONS['imports-validate'],
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
