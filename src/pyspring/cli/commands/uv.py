"""
PySpring uv Command
"""
from .uv_ops.core import run


def register_subcommand(subparsers):
    """注册 uv 子命令"""
    parser = subparsers.add_parser(
        'uv',
        help='Manage uv virtual environment',
        description='Manage uv virtual environment lifecycle'
    )

    uv_subparsers = parser.add_subparsers(dest='uv_command', required=True, help='Sub-commands')

    # Setup
    setup_parser = uv_subparsers.add_parser('setup', help='Setup uv environment (create venv, install deps)')
    setup_parser.add_argument('--dev', action='store_true', help='Install development dependencies')
    setup_parser.add_argument('--rebuild', action='store_true', help='Recreate existing environment')

    # Rebuild
    uv_subparsers.add_parser('rebuild', help='Rebuild environment (clean and setup)')

    # Install
    install_parser = uv_subparsers.add_parser('install', help='Install PySpring dependencies')
    install_parser.add_argument('--dev', action='store_true', help='Install development dependencies')

    # Status
    uv_subparsers.add_parser('status', help='Show current environment status')

    parser.set_defaults(func=run)
