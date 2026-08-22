from ..core.commands.base import BaseCommand
from .ops.meta.check import CliCheckCommand


class MetaCommand(BaseCommand):
    name = "meta"
    help = "Meta-utilities for PySpring CLI itself"

    subcommands = [CliCheckCommand]
