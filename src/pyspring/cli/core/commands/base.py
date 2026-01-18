import argparse
from abc import ABC
from dataclasses import dataclass
from typing import List, Union, Any, Type, Dict, Optional


@dataclass
class CommandArg:
    """Represents a command line argument"""
    flags: Union[str, List[str]]  # e.g. "path" or ["-f", "--force"]
    help: str = ""
    default: Any = None
    action: str = None  # defaults to 'store' usually, but determined by add_argument
    type: Any = None
    required: bool = False
    nargs: Union[str, int] = None
    choices: List[Any] = None
    metavar: str = None
    dest: str = None

    def add_to_parser(self, parser):
        args = [self.flags] if isinstance(self.flags, str) else self.flags
        kwargs: Dict[str, Any] = {'help': self.help}

        if self.action:
            kwargs['action'] = self.action

        if self.default is not None:
            kwargs['default'] = self.default

        if self.required:
            kwargs['required'] = True

        if self.nargs is not None:
            kwargs['nargs'] = self.nargs

        if self.choices:
            kwargs['choices'] = self.choices

        if self.metavar:
            kwargs['metavar'] = self.metavar

        if self.dest:
            kwargs['dest'] = self.dest

        # Only add type if it's not a flag that doesn't take values
        if self.action not in ['store_true', 'store_false', 'count', 'help']:
            if self.type:
                kwargs['type'] = self.type

        parser.add_argument(*args, **kwargs)


class BaseCommand(ABC):
    """Base class for all PySpring CLI commands"""
    name: str = None
    help: str = None
    description: str = None
    arguments: List[CommandArg] = []
    subcommands: List[Type['BaseCommand']] = []

    # Custom formatter class for argparse
    formatter_class = argparse.HelpFormatter

    # Internal reference to subparsers action for help printing
    _subparsers_action: Optional[Any] = None

    def run(self, args: argparse.Namespace):
        """Main execution logic"""
        if hasattr(self, '_subparsers_action'):
            from ..ui import print_friendly_subcommand_help
            print_friendly_subcommand_help(self._subparsers_action, prog_name=f"pyspring {self.name}")
        else:
            print(f"Command {self.name} not implemented.")

    def print_help(self):
        """Print help for this command"""
        if hasattr(self, '_subparsers_action'):
            from ..ui import print_friendly_subcommand_help
            # TODO: Decouple 'pyspring' name
            print_friendly_subcommand_help(self._subparsers_action, prog_name=f"pyspring {self.name}")

    @classmethod
    def register(cls, subparsers):
        """Register command to argparse subparsers"""
        if not cls.name:
            raise ValueError(f"Command {cls.__name__} must have a name")

        parser = subparsers.add_parser(
            cls.name,
            help=cls.help,
            description=cls.description or cls.help,
            formatter_class=cls.formatter_class
        )

        # Add arguments
        for arg in cls.arguments:
            arg.add_to_parser(parser)

        # Instantiate and set default function
        command_instance = cls()

        # Special handling for commands with subcommands (like 'check') that might also run on its own (like 'check --all')
        # We wrap the run method to handle the dispatching or fallback

        if cls.subcommands:
            cls._register_subcommands(parser, command_instance)
        else:
            parser.set_defaults(func=command_instance.run)

    @classmethod
    def _register_subcommands(cls, parser, instance):
        """Register nested subcommands"""
        sub_dest = f"{cls.name}_command"

        subparsers = parser.add_subparsers(
            title="Available Commands",
            dest=sub_dest,
            required=False,  # We allow parent command to run if no subcommand provided
            metavar='<command>'
        )

        # Store action for help printing
        instance._subparsers_action = subparsers

        for sub_cmd in cls.subcommands:
            sub_cmd.register(subparsers)

        # If the parent command has its own run logic (e.g. check --all),
        # we need to be careful. Argparse executes the func in set_defaults.
        # If a subcommand is chosen, its func is executed.
        # If no subcommand is chosen, we want the parent logic or help.

        # We set a default func for the parent parser. 
        # CAUTION: If a subcommand is selected, argparse overwrites 'func'.
        # So this default only triggers if NO subcommand is matched.
        parser.set_defaults(func=lambda args: cls._dispatch(args, instance))

    @staticmethod
    def _dispatch(args, instance):
        """Dispatch execution to subcommands or parent command"""
        return instance.run(args)
