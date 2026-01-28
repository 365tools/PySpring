from .ops.dev.exports import sync_exports
from .ops.dev.sync import sync_templates
from .ops.dev.verify import verify_pyproject
from ..core.commands.base import BaseCommand, CommandArg


class SyncTemplatesCommand(BaseCommand):
    name = "templates-sync"
    help = "Synchronize project files with templates"

    def run(self, args):
        sync_templates(args)


class VerifyConfigCommand(BaseCommand):
    name = "config-verify"
    help = "Validate pyproject.toml generation logic"

    def run(self, args):
        verify_pyproject(args)


class InitSyncCommand(BaseCommand):
    name = "init-sync"
    help = "Auto-generate __init__.py package exports"
    arguments = [
        CommandArg('path', nargs='?', default='.', help='Path to package directory (default: current dir)'),
        CommandArg('--fixed', action='store_true', help='Generate fixed explicit exports'),
        CommandArg('--dynamic', action='store_true', help='Use dynamic auto-import (default)'),
        CommandArg('--output', action='store_true', help='Generate standard __all__ format (preserves comments)'),
    ]

    def run(self, args):
        sync_exports(args)


class DevCommand(BaseCommand):
    name = "dev"
    help = "Internal development utilities"
    description = "Tools for PySpring framework development"

    subcommands = [
        SyncTemplatesCommand,
        VerifyConfigCommand,
        InitSyncCommand
    ]
