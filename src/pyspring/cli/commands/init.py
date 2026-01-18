"""
PySpring CLI Init Command Registration
"""
import argparse

from .ops.init.core import run
from ..core.commands.base import BaseCommand, CommandArg


class InitCommand(BaseCommand):
    name = "init"
    help = "Scaffold new PySpring project structure"
    description = """
Initialize PySpring Project Structure and Configuration Files.

Examples:
  # Initialize current directory
  pyspring init

  # Initialize specific directory
  pyspring init /path/to/project

  # Force overwrite existing files
  pyspring init --force
  
  # Create minimal configuration
  pyspring init --minimal
  
  # Skip .env file generation
  pyspring init --skip-env
    """
    formatter_class = argparse.RawDescriptionHelpFormatter

    arguments = [
        CommandArg(
            flags='target_dir',
            nargs='?',
            default=None,
            help='Target directory (default: current directory)'
        ),
        CommandArg(
            flags=['-f', '--force'],
            action='store_true',
            help='Force overwrite existing files'
        ),
        CommandArg(
            flags=['-m', '--minimal'],
            action='store_true',
            help='Create minimal configuration only'
        ),
        CommandArg(
            flags='--skip-env',
            action='store_true',
            help='Skip .env file generation'
        )
    ]

    def run(self, args: argparse.Namespace):
        run(args)
