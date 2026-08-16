"""
Help System Utilities
"""
import argparse
import sys
from typing import Dict, List, Optional, Tuple

from .console import Colors, print_title


def print_standard_command_help(
        title: Optional[str],
        description: Optional[str],
        usage: List[Tuple[str, str]],
        options: List[Tuple[str, str]] | None = None,
        subcommands: Dict[str, str] | None = None,
        checks: List[Tuple[str, bool]] | None = None,
        tips: List[str] | None = None
):
    """
    Print a standardized help interface for any CLI command.
    """
    if title:
        print_title(title)

    if description:
        print(f"\n{description}")

    # 1. Environment Checks (if provided)
    if checks:
        print(f"\n{Colors.BOLD}[Environment Check]{Colors.ENDC}")
        for msg, passed in checks:
            if passed:
                print(f"  {Colors.OKGREEN}[OK] {msg}{Colors.ENDC}")
            else:
                print(f"  {Colors.FAIL}[FAIL] {msg}{Colors.ENDC}")

    # 2. Usage Section
    if usage:
        print(f"\n{Colors.BOLD}[Usage]{Colors.ENDC}")
        max_len = max(len(u[0]) for u in usage) if usage else 0
        for cmd, desc in usage:
            print(f"  {Colors.OKBLUE}{cmd:<{max_len}}{Colors.ENDC} : {desc}")

    # 3. Subcommands Section (if provided)
    if subcommands:
        print(f"\n{Colors.BOLD}[Available Commands]{Colors.ENDC}")
        max_len = max(len(k) for k in subcommands.keys()) if subcommands else 0
        for name, desc in sorted(subcommands.items()):
            print(f"  {Colors.OKCYAN}> {name:<{max_len}}{Colors.ENDC} : {desc}")

    # 4. Options Section (if provided)
    if options:
        print(f"\n{Colors.BOLD}[Options]{Colors.ENDC}")
        max_len = max(len(o[0]) for o in options) if options else 0
        for flag, desc in options:
            print(f"  {Colors.OKCYAN}{flag:<{max_len}}{Colors.ENDC} : {desc}")

    # 5. Tips/Warnings
    if tips:
        print()
        for tip in tips:
            print(f"{Colors.WARNING}Tip: {tip}{Colors.ENDC}")


def print_friendly_subcommand_help(action, prog_name=None):
    """
    Print a friendly list of available subcommands to stderr.
    Args:
        action: The argparse._SubParsersAction object
        prog_name: The program name (e.g. 'pyspring')
    """
    if prog_name is None:
        prog_name = sys.argv[0] if sys.argv else 'pyspring'

    # Get choices
    choices = action.choices
    if not choices:
        return

    # Create subcommands dict
    subcommands = {}

    choices_actions = getattr(action, '_choices_actions', [])
    for sub_action in choices_actions:
        subcommands[sub_action.dest] = sub_action.help

    # Tips customization
    tips = []
    if action.dest == 'check_command':
        tips.append(f"Use --all to run all checks: '{prog_name} check --all'")
        tips.append(f"Use '{prog_name} check <command> --help' for details on a specific command.")
    else:
        tips.append(f"Use '{prog_name} <command> --help' for details on a specific command.")

    print_standard_command_help(
        title=None,
        description="  Missing command. Please specify one of the following:",
        usage=[],  # No usage section for this simple error prompt
        subcommands=subcommands,
        tips=tips
    )


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
        for action in current_parser._actions:
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
