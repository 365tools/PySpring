"""
PySpring Check Command
"""
from .ops.check.basedpyright import run_check_basedpyright
from .ops.check.circular import run_check_circular
from .ops.check.diagnose import run as run_diagnose_check
from .ops.check.encoding import run_check_encoding
from .ops.check.explicit import run_check_explicit_imports
from .ops.check.imports.reset import run_import_reset
from .ops.check.imports.validate import run_validate_imports
from .ops.check.lift import run_lift_imports
from .ops.check.refactor import run_check_refactor
from .ops.check.references import run_check_references
from ..core.commands.base import BaseCommand, CommandArg
from ..core.parser.formatter import SortedHelpFormatter
from ..core.ui.console import print_title, print_error
from ..core.ui.help import print_friendly_subcommand_help
from ..core.ui.report import print_check_summary

# Shared descriptions for CLI help and summary
CHECK_DESCRIPTIONS = {
    'encoding': 'Validate file encoding (UTF-8 compliance)',
    'diagnose': 'Diagnose development environment and Python setup issues',
    'imports-circular': 'Detect circular import dependencies',
    'imports-explicit': 'Refactor: Convert package imports to explicit submodules',
    'imports-lift': 'Refactor: Move local imports to module top-level',
    'imports-reset': 'Destructively reset and reconstruct "pyspring" imports',
    'imports-refactor': 'Convert between absolute and relative imports',
    'imports-validate': 'Validate imports and resolve missing modules',
    'references': 'Identify and fix unresolved symbol references',
    'basedpyright': 'Deep type checking via basedpyright (reports IDE-style diagnostics)',
}


class CheckReferencesCommand(BaseCommand):
    name = "references"
    help = CHECK_DESCRIPTIONS['references']
    description = 'Scan project for missing imports and undefined names'
    arguments = [
        CommandArg('path', nargs='?', default='.'),
        CommandArg('--fix', action='store_true', help='Attempt to automatically fix missing imports for standard libraries'),
        CommandArg('--strict', action='store_true', help='Fail if any issues are found (including Mypy issues)'),
        CommandArg('--whitelist', help='Pipe-separated list of issue categories to include (e.g. "Static Method|Type Mismatch")')
    ]

    def run(self, args):
        run_check_references(args)


class CheckBasedPyrightCommand(BaseCommand):
    name = "basedpyright"
    help = CHECK_DESCRIPTIONS['basedpyright']
    description = 'Run deep type checking via basedpyright across all files. Reports IDE-style diagnostics (deprecated types, explicit Any, abstract usage, unknown types, etc).'
    arguments = [
        CommandArg('path', nargs='?', default='.'),
        CommandArg('--severity', choices=['error', 'warning', 'all'], default='error', help='Minimum severity to report (default: error)'),
        CommandArg('--rules', default='', metavar='RULE1,RULE2', help='Only report specific pyright rules, comma-separated (e.g. "reportDeprecated,reportExplicitAny")')
    ]

    def run(self, args):
        run_check_basedpyright(args)


class CheckEncodingCommand(BaseCommand):
    name = "encoding"
    help = CHECK_DESCRIPTIONS['encoding']
    description = 'Scan project files for encoding issues (non-utf-8 or BOM)'
    arguments = [
        CommandArg('target', nargs='?', default='.'),
        CommandArg('--fix', action='store_true', help='Automatically fix encoding issues (convert to utf-8 without BOM)')
    ]

    def run(self, args):
        run_check_encoding(args)


class CheckDiagnoseCommand(BaseCommand):
    name = "diagnose"
    help = CHECK_DESCRIPTIONS['diagnose']
    description = 'Diagnose Python environment, installation, and path issues'

    def run(self, args):
        run_diagnose_check(args)


class CheckCircularCommand(BaseCommand):
    name = "imports-circular"
    help = CHECK_DESCRIPTIONS['imports-circular']
    description = "Scan project for circular imports using static analysis (AST)"
    arguments = [
        CommandArg('path', nargs='?', default='.')
    ]

    def run(self, args):
        run_check_circular(args)


class CheckExplicitCommand(BaseCommand):
    name = "imports-explicit"
    help = CHECK_DESCRIPTIONS['imports-explicit']
    description = 'Convert package-level imports (from pkg import Item) to submodule imports (from pkg.sub import Item) to bypass dynamic __init__ issues.'
    arguments = [
        CommandArg('path', nargs='?', default='.'),
        CommandArg('--fix', action='store_true')
    ]

    def run(self, args):
        run_check_explicit_imports(args)


class CheckRefactorCommand(BaseCommand):
    name = "imports-refactor"
    help = CHECK_DESCRIPTIONS['imports-refactor']
    description = 'Refactor imports to be either absolute (default) or relative.'
    arguments = [
        CommandArg('path', nargs='?', default='.'),
        CommandArg('--to-relative', action='store_true'),
        CommandArg('--to-absolute', action='store_true'),
        CommandArg('--level', type=int, default=2, metavar=''),
        CommandArg('--fix', action='store_true')
    ]

    def run(self, args):
        run_check_refactor(args)


class CheckLiftCommand(BaseCommand):
    name = "imports-lift"
    help = CHECK_DESCRIPTIONS['imports-lift']
    description = 'Scan for local imports in functions and move them to top-level if safe (no circular dependencies). Adds comments if unsafe.'
    arguments = [
        CommandArg('target', nargs='?', default='.'),
        CommandArg('--fix', action='store_true')
    ]

    def run(self, args):
        run_lift_imports(args)


class CheckValidateCommand(BaseCommand):
    name = "imports-validate"
    help = CHECK_DESCRIPTIONS['imports-validate']
    description = 'Comprehensive imports check. Detects missing modules (ModuleNotFoundError) and can auto-resolve broken paths.'
    arguments = [
        CommandArg('target', nargs='?', default='.'),
        CommandArg('--mode', choices=['static', 'dynamic', 'all'], default='all'),
        CommandArg('--fix', action='store_true'),
        CommandArg('--exclude', default='', metavar='')
    ]

    def run(self, args):
        run_validate_imports(args)


class CheckResetCommand(BaseCommand):
    name = "imports-reset"
    help = CHECK_DESCRIPTIONS['imports-reset']
    description = 'Destructively remove all "pyspring" imports and re-index project to find correct locations. Use when package structure has changed significantly.'
    arguments = [
        CommandArg('path', nargs='?', default='.'),
        CommandArg(['-f', '--force'], action='store_true', help='Force delete satisfying imports as well (nuclear option)'),
        CommandArg('--fix', action='store_true', help='Execute removal and reconstruction')
    ]

    def run(self, args):
        run_import_reset(args)


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
        self.severity = 'error'
        self.rules = ''


def run_all_checks(args, subparsers_action=None):
    """Execution logic for check --all"""
    if not args.all:
        if getattr(args, 'check_command', None) is None:
            if subparsers_action:
                print_friendly_subcommand_help(subparsers_action, prog_name='pyspring')
            elif getattr(args, '_subparsers_action', None):  # Fallback if passed via instance
                print_friendly_subcommand_help(args._subparsers_action, prog_name='pyspring')
            return

    print_title("PySpring Health Diagnosis (All Checks)")

    # Registry from local imports
    # Rebuilding it dynamically or keeping static? keeping static for now inside function
    registry = {
        'basedpyright': run_check_basedpyright,
        'encoding': run_check_encoding,
        'diagnose': run_diagnose_check,
        'imports-circular': run_check_circular,
        'imports-explicit': run_check_explicit_imports,
        'imports-lift': run_lift_imports,
        'imports-refactor': run_check_refactor,
        'imports-validate': run_validate_imports,
        'references': run_check_references,
    }

    results = []
    sorted_keys = sorted(registry.keys())

    for name in sorted_keys:
        func = registry[name]
        print(f"\n>> Running Check: {name}...")
        try:
            mock_args = CheckArgs()
            result = func(mock_args)
            results.append((name, result))
        except Exception as e:
            print_error(f"Check '{name}' crashed: {e}")
            results.append((name, False))

    fix_commands = {
        'encoding': '--fix',
        'imports-explicit': '--fix',
        'imports-lift': '--fix',
        'imports-refactor': '--fix',
        'imports-validate': '--fix',
        'references': '--fix'
    }

    print_check_summary(results, fix_commands)


class CheckCommand(BaseCommand):
    name = "check"
    help = "Check project health"
    description = "Check project health and code integrity"
    formatter_class = SortedHelpFormatter

    arguments = [
        CommandArg('--all', action='store_true', help='Run all available checks in sequence and report summary')
    ]

    subcommands = [
        CheckReferencesCommand,
        CheckBasedPyrightCommand,
        CheckEncodingCommand,
        CheckDiagnoseCommand,
        CheckCircularCommand,
        CheckExplicitCommand,
        CheckRefactorCommand,
        CheckLiftCommand,
        CheckValidateCommand,
        CheckResetCommand,
    ]

    def run(self, args):
        run_all_checks(args, getattr(self, '_subparsers_action', None))
