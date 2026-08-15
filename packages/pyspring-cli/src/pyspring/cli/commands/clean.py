from .ops.clean.cache import clean_project_cache
from .ops.clean.imports import run_clean_imports
from ..core.commands.base import BaseCommand, CommandArg
from ..core.parser.formatter import SortedHelpFormatter


class CleanCacheCommand(BaseCommand):
    name = "cache"
    help = "Clear system and framework caches"
    description = "Remove project cache directories"
    arguments = [
        CommandArg(['-v', '--verbose'], action='store_true', help='Show detailed output')
    ]

    def run(self, args):
        clean_project_cache(args.verbose)


class CleanImportsCommand(BaseCommand):
    name = "imports-unused"
    help = "Remove detected unused import statements"
    description = "Scanning and removing unused import statements"
    arguments = [
        CommandArg('path', nargs='?', default='.', help='Path to clean (default: current directory)'),
        CommandArg(['-v', '--verbose'], action='store_true', help='Show detailed output')
    ]

    def run(self, args):
        run_clean_imports(args)


class CleanCommand(BaseCommand):
    name = "clean"
    help = "Remove artifacts, caches, and unused code"
    description = "Remove temporary files or clean unused codes"
    formatter_class = SortedHelpFormatter

    subcommands = [
        CleanCacheCommand,
        CleanImportsCommand
    ]
