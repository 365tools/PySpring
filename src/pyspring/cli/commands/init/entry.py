"""
PySpring CLI Init Command Registration
"""
from .core import run


def register_subcommand(subparsers):
    """注册 init 子命令"""
    import argparse
    parser = subparsers.add_parser(
        'init',
        help='Initialize PySpring project configuration',
        description="""
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
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'target_dir',
        nargs='?',
        default=None,
        help='Target directory (default: current directory)'
    )

    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='Force overwrite existing files'
    )

    parser.add_argument(
        '-m', '--minimal',
        action='store_true',
        help='Create minimal configuration only'
    )

    parser.add_argument(
        '--skip-env',
        action='store_true',
        help='Skip .env file generation'
    )

    parser.set_defaults(func=run)
