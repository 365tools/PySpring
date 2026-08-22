import argparse
import re
import sys

from ..ui.help import print_friendly_subcommand_help


class FriendlyArgumentParser(argparse.ArgumentParser):
    """
    Custom ArgumentParser that provides friendlier error messages and suggestions.
    """

    def error(self, message):
        """
        Override error method to provide helpful suggestions when arguments are missing.
        """
        # Initial error banner
        # We don't print the standard "usage: ..." here immediately to avoid clutter if we want a custom one

        # Check for missing required arguments (subcommands)
        if "the following arguments are required" in message:
            # Extract the missing argument name(s)
            match = re.search(r": (.+)", message)
            missing_args = match.group(1).split(", ") if match else []

            # Check if one of missing args allows subcommands
            subparser_action = self._find_subparser_action(missing_args)

            if subparser_action:
                self._print_friendly_subcommand_help(subparser_action)
                sys.exit(2)

        # Fallback for other errors (like invalid choice)
        if "invalid choice" in message:
            # handle invalid command
            match = re.search(r"invalid choice: '(.+?)'", message)
            invalid_cmd = match.group(1) if match else "command"
            print(f"\n❌ Unknown command: '{invalid_cmd}'\n", file=sys.stderr)
            print("Did you mean one of these?", file=sys.stderr)
            # Logic to find close matches could go here, for now just print help
            self.print_help(sys.stderr)
            sys.exit(2)

        # Default fallback
        print(f"\n❌ Error: {message}\n", file=sys.stderr)
        self.print_help(sys.stderr)
        sys.exit(2)

    def _find_subparser_action(self, missing_args):
        """Find the subparser action corresponding to the missing argument"""
        # Search safely in _actions
        for action in self._actions:
            if isinstance(action, argparse._SubParsersAction):
                # Check dest (e.g. 'check_command')
                if action.dest in missing_args:
                    return action
                # Check metavar (e.g. '<check_command>')
                if action.metavar and action.metavar in missing_args:
                    return action
        return None

    def _print_friendly_subcommand_help(self, action):
        """Print a friendly list of available subcommands"""
        print_friendly_subcommand_help(action, self.prog)
