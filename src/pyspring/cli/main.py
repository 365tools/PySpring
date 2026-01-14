"""
PySpring CLI Main Entry Point
"""
import argparse
import sys

from .commands import init, uv, check, clean, security, dev
from .core.formatter import GroupedHelpFormatter


def main():
    """CLI Entry Point"""
    parser = argparse.ArgumentParser(
        prog='pyspring',
        description='PySpring Framework Command Line Interface',
        epilog='For more information, visit https://github.com/365tools/PySpring',
        formatter_class=GroupedHelpFormatter
    )

    parser.add_argument('-v', '--version', action='version', version='PySpring 1.0.0')

    subparsers = parser.add_subparsers(
        title='Available Commands',
        dest='command',
        required=True,
        metavar='<command>'
    )

    # Register subcommands from tools
    uv.register_subcommand(subparsers)
    init.register_subcommand(subparsers)
    check.register_subcommand(subparsers)
    clean.register_subcommand(subparsers)
    security.register_subcommand(subparsers)

    # Internal tools for PySpring framework development
    dev.register_subcommand(subparsers)

    # Show help if no arguments provided
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Parse arguments
    args = parser.parse_args()

    # Execute the registered function for the subcommand
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

