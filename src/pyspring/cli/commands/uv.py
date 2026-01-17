"""
PySpring uv Command
"""
from .ops.uv.core import run


def register_subcommand(subparsers):
    """Register uv subcommand"""
    parser = subparsers.add_parser(
        'uv',
        help='Manage UV environment and dependencies',
        description='Manage uv virtual environment lifecycle'
    )

    uv_subparsers = parser.add_subparsers(dest='uv_command', required=True, help='Sub-commands')

    # Setup
    setup_parser = uv_subparsers.add_parser('setup', help='Initialize environment and install dependencies')
    setup_parser.add_argument('--dev', action='store_true', help='Install development dependencies')
    setup_parser.add_argument('--rebuild', action='store_true', help='Recreate existing environment')

    # Rebuild
    uv_subparsers.add_parser('rebuild', help='Re-initialize environment from scratch')

    # Install
    install_parser = uv_subparsers.add_parser('install', help='Install project dependencies to environment')
    install_parser.add_argument('--dev', action='store_true', help='Install development dependencies')

    # Status
    uv_subparsers.add_parser('status', help='Display environment configuration status')

    parser.set_defaults(func=run)
