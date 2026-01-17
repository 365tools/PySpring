"""
PySpring Internal Development Command
"""
from .dev_ops.exports import sync_exports
from .dev_ops.refactor import refactor_imports
from .dev_ops.sync import sync_templates
from .dev_ops.verify import verify_pyproject


def register_subcommand(subparsers):
    """Register dev subcommand"""
    parser = subparsers.add_parser(
        'dev',
        help='Internal development utilities',  # Revert SUPPRESS
        description='Tools for PySpring framework development'
    )

    dev_subparsers = parser.add_subparsers(dest='dev_command', required=True, help='Sub-commands')

    # Sync Templates
    sync_parser = dev_subparsers.add_parser('templates-sync', help='Synchronize project files with templates')
    sync_parser.set_defaults(func=sync_templates)

    # Verify Config
    verify_parser = dev_subparsers.add_parser('config-verify', help='Validate pyproject.toml generation logic')
    verify_parser.set_defaults(func=verify_pyproject)

    # Sync Exports (Auto-Init)
    init_parser = dev_subparsers.add_parser('init-sync', help='Auto-generate __init__.py package exports')
    init_parser.add_argument('path', help='Path to package directory')
    init_parser.add_argument('--fixed', action='store_true', help='Generate fixed explicit exports')
    init_parser.add_argument('--dynamic', action='store_true', help='Use dynamic auto-import (default)')
    init_parser.set_defaults(func=sync_exports)

    # Refactor Imports
    refactor_parser = dev_subparsers.add_parser('imports-refactor', help='Convert between absolute and relative imports')
    refactor_parser.add_argument('path', nargs='?', default='src', help='Directory to refactor (default: src)')
    refactor_parser.add_argument('--to-relative', action='store_true', help='Convert absolute imports to relative')
    refactor_parser.add_argument('--to-absolute', action='store_true', help='Convert relative imports to absolute')
    refactor_parser.set_defaults(func=refactor_imports)
