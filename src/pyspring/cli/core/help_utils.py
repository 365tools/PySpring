"""
Help Utilities
"""
import argparse
import sys


def print_recursive_help(parser, file=None):
    """
    Recursively print help for all commands in the parser hierarchy
    """
    if file is None:
        file = sys.stdout

    print("=" * 80, file=file)
    print("PySpring CLI Full Reference", file=file)
    print("=" * 80, file=file)
    print("\n", file=file)

    # Print the top-level help
    print("Global Help:", file=file)
    print("-" * 20, file=file)
    parser.print_help(file=file)
    print("\n", file=file)

    def _walk_actions(current_parser):
        # Iterate over all actions in the parser
        # Accessing protected member _actions is required because argparse 
        # doesn't expose a public API to inspect registered actions.
        for action in current_parser._actions:  # noqa
            # Check if the action is a subparser action (contains subcommands)
            if isinstance(action, argparse._SubParsersAction):
                # Retrieve the mapping of command names to their parsers
                choices = action.choices
                if not choices:
                    continue

                # Iterate over each subcommand
                for command_name, subparser in choices.items():
                    # Separator for readability
                    print("\n" + "-" * 80, file=file)
                    # subparser.prog automatically includes the hierarchical command name (e.g. "pyspring init")
                    print(f"Command: {subparser.prog}", file=file)
                    print("-" * 80, file=file)

                    # Print help for this specific subcommand
                    subparser.print_help(file=file)
                    print("\n", file=file)

                    # Recursively walk down
                    _walk_actions(subparser)

    _walk_actions(parser)
