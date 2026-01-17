import argparse
from operator import attrgetter


class SortedHelpFormatter(argparse.HelpFormatter):
    """
    Formatter that automatically sorts arguments and subcommands alphabetically.
    """

    def add_arguments(self, actions):
        # Sort arguments: flags first, then others. Sort by the first flag or dest.
        def sort_key(action):
            # Prefer sorting by option string (e.g., -a, --all)
            if action.option_strings:
                return action.option_strings[0]
            # Fallback to dest for positional args
            return action.dest

        actions = sorted(actions, key=sort_key)
        super().add_arguments(actions)

    def _format_action(self, action):
        # Sort subcommands if this is a subparser action
        if isinstance(action, argparse._SubParsersAction):
            # _choices_actions is the list used by HelpFormatter to print subcommands
            # We sort this list in-place to affect the output order
            action._choices_actions.sort(key=attrgetter('dest'))

        return super()._format_action(action)


class GroupedHelpFormatter(SortedHelpFormatter):
    """
    Format help to handle groups of commands.
    Inherits sorting capabilities for non-grouped items and arguments.
    """

    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            # Define groups logic (Manual order for these specific groups)
            groups = [
                ("User Commands", ["uv", "init", "check", "clean", "security"]),
                ("Internal Commands", ["dev"]),
            ]

            parts = []
            cmds = action.choices  # dict mapping name -> parser

            help_lookup = {}
            for sub_action in action._choices_actions:
                help_lookup[sub_action.dest] = sub_action.help

            shown_cmds = set()

            for title, cmd_names in groups:
                group_cmds = [c for c in cmd_names if c in cmds]

                visible_cmds = []
                for name in group_cmds:
                    help_str = help_lookup.get(name, '')
                    if help_str is not argparse.SUPPRESS:
                        visible_cmds.append(name)

                if visible_cmds:
                    parts.append(f'\n{title}:\n')
                    for name in visible_cmds:
                        shown_cmds.add(name)
                        help_str = help_lookup.get(name, '')
                        parts.append(f'  {name:<12} {help_str}\n')

            # Remaining - Sort them alphabetically!
            remaining = [c for c in cmds if c not in shown_cmds]
            remaining.sort()
            
            visible_remaining = []
            for name in remaining:
                help_str = help_lookup.get(name, '')
                if help_str is not argparse.SUPPRESS:
                    visible_remaining.append(name)

            if visible_remaining:
                parts.append(f'\nOther Commands:\n')
                for name in visible_remaining:
                    help_str = help_lookup.get(name, '')
                    parts.append(f'  {name:<12} {help_str}\n')

            return "".join(parts)

        return super()._format_action(action)

