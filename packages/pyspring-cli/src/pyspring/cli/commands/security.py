from ..core.commands.base import BaseCommand
from .ops.security.encryption import generate_encryption_key


class GenerateKeyCommand(BaseCommand):
    name = "gen-key"
    help = "Generate new high-entropy encryption keys"

    def run(self, args):
        generate_encryption_key(args)


class SecurityCommand(BaseCommand):
    name = "security"
    help = "Manage security configurations and encryption keys"
    description = "Security utilities for PySpring"

    subcommands = [GenerateKeyCommand]
