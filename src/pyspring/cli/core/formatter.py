import argparse


class GroupedHelpFormatter(argparse.HelpFormatter):
    """
    Format help to handle groups of commands
    """

    def _format_action(self, action):
        if isinstance(action, argparse._SubParsersAction):
            # Define groups logic
            groups = [
                ("User Commands", ["init", "uv", "check", "clean", "security"]),
                ("Internal Commands", ["dev"]),
            ]

            parts = []
            cmds = action.choices

            help_lookup = {}
            for sub_action in action._choices_actions:
                help_lookup[sub_action.dest] = sub_action.help

            shown_cmds = set()

            for title, cmd_names in groups:
                group_cmds = [c for c in cmd_names if c in cmds]

                # Filter out suppressed commands unless we are in the group explicitly
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

            # Remaining
            remaining = [c for c in cmds if c not in shown_cmds]
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
