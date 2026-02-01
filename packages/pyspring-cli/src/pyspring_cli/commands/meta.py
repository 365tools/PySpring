from .ops.meta.check import CliCheckCommand
from ..core.commands.base import BaseCommand


class MetaCommand(BaseCommand):
    name = "meta"
    help = "Meta-utilities for PySpring CLI itself"

    subcommands = [
        CliCheckCommand
    ]
