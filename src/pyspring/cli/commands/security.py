"""
PySpring Security Command
"""
from .security_ops.encryption import generate_encryption_key


def register_subcommand(subparsers):
    """Register security subcommand"""
    parser = subparsers.add_parser(
        'security',
        help='Manage security configurations and encryption keys',
        description='Security utilities for PySpring'
    )

    security_subparsers = parser.add_subparsers(dest='security_command', required=True, help='Sub-commands')

    # Generate Key
    gen_key_parser = security_subparsers.add_parser('gen-key', help='Generate new high-entropy encryption keys')
    gen_key_parser.set_defaults(func=generate_encryption_key)
