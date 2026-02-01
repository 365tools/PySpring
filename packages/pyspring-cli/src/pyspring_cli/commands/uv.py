from .ops.uv.core import (
    setup_uv_env,
    rebuild_uv_env,
    install_pyspring,
    show_uv_status,
    print_activation_hint
)
from ..core.commands.base import BaseCommand, CommandArg


class UvSetupCommand(BaseCommand):
    name = "setup"
    help = "Initialize environment and install dependencies"
    arguments = [
        CommandArg('--dev', action='store_true', help='Install development dependencies'),
        CommandArg('--rebuild', action='store_true', help='Recreate existing environment')
    ]

    def run(self, args):
        setup_uv_env(dev_mode=args.dev, rebuild=args.rebuild)


class UvRebuildCommand(BaseCommand):
    name = "rebuild"
    help = "Re-initialize environment from scratch"

    def run(self, args):
        rebuild_uv_env()


class UvInstallCommand(BaseCommand):
    name = "install"
    help = "Install project dependencies to environment"
    arguments = [
        CommandArg('--dev', action='store_true', help='Install development dependencies')
    ]

    def run(self, args):
        install_pyspring(dev_mode=args.dev)
        print("\n✅ Install complete!")
        print_activation_hint()


class UvStatusCommand(BaseCommand):
    name = "status"
    help = "Display environment configuration status"
    arguments = [
        CommandArg(
            "module",
            nargs="?",
            help="Show detailed information for a specific module"
        )
    ]

    def run(self, args):
        show_uv_status(args.module)


class UvCommand(BaseCommand):
    name = "uv"
    help = "Manage UV environment and dependencies"
    description = "Manage uv virtual environment lifecycle"

    subcommands = [
        UvSetupCommand,
        UvRebuildCommand,
        UvInstallCommand,
        UvStatusCommand
    ]
