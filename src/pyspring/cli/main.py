"""
PySpring CLI Main Entry Point
"""
import argparse
import sys

from .commands import init, diagnose, uv_manager, check


def main():
    """CLI Entry Point"""
    parser = argparse.ArgumentParser(
        prog='pyspring',
        description='PySpring Framework Command Line Interface',
        epilog='For more information, visit https://github.com/365tools/PySpring'
    )

    parser.add_argument('-v', '--version', action='version', version='PySpring 1.0.0')

    subparsers = parser.add_subparsers(
        title='Available Commands',
        dest='command',
        required=True,
        metavar='<command>'
    )

    # Register subcommands from tools
    uv_manager.register_subcommand(subparsers)
    init.register_subcommand(subparsers)
    check.register_subcommand(subparsers)
    diagnose.register_subcommand(subparsers)

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

