"""
PySpring CLI Main Entry Point
"""
import sys

from .core.commands.loader import load_commands
from .core.parser.custom import FriendlyArgumentParser
from .core.parser.formatter import GroupedHelpFormatter


def main():
    """CLI Entry Point"""
    parser = FriendlyArgumentParser(
        prog='pyspring',
        description='PySpring Framework Command Line Interface',
        epilog='For more information, visit https://github.com/365tools/PySpring',
        formatter_class=GroupedHelpFormatter
    )

    parser.add_argument('-v', '--version', action='version', version='PySpring 1.0.0')
    parser.add_argument('--all', action='store_true', help='Show detailed help for all commands')

    subparsers = parser.add_subparsers(
        title='Available Commands',
        dest='command',
        required=False,
        metavar='<command>'
    )

    # Register subcommands dynamically
    load_commands(subparsers)

    # Show help if no arguments provided
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Parse arguments
    args = parser.parse_args()

    # Handle --all flag (Global Help) ONLY if no subcommand is selected
    if hasattr(args, 'all') and args.all and not args.command:
        from .core.ui.help import print_recursive_help
        print_recursive_help(parser)
        sys.exit(0)

    # If no command is selected (and not --all), show help
    if not args.command:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Execute the registered function for the subcommand
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

