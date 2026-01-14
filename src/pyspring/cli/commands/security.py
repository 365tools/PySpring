"""
PySpring Security Command
"""
from .security_ops import generate_encryption_key


def register_subcommand(subparsers):
    """注册 security 子命令"""
    parser = subparsers.add_parser(
        'security',
        help='Manage security related operations',
        description='Security utilities for PySpring'
    )

    security_subparsers = parser.add_subparsers(dest='security_command', required=True, help='Sub-commands')

    # Generate Key
    gen_key_parser = security_subparsers.add_parser('gen-key', help='Generate a new JWT encryption key')
    gen_key_parser.set_defaults(func=generate_encryption_key)
