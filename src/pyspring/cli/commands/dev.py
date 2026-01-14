"""
PySpring Internal Development Command
"""
from .dev_ops import sync_templates, verify_pyproject, sync_exports, refactor_imports


def register_subcommand(subparsers):
    """注册 dev 子命令"""
    parser = subparsers.add_parser(
        'dev',
        help='Internal development tools',  # Revert SUPPRESS
        description='Tools for PySpring framework development'
    )

    dev_subparsers = parser.add_subparsers(dest='dev_command', required=True, help='Sub-commands')

    # Sync Templates
    sync_parser = dev_subparsers.add_parser('sync-templates', help='Sync project files to templates')
    sync_parser.set_defaults(func=sync_templates)

    # Verify Config
    verify_parser = dev_subparsers.add_parser('verify-config', help='Verify pyproject.toml generation')
    verify_parser.set_defaults(func=verify_pyproject)

    # Sync Exports (Auto-Init)
    init_parser = dev_subparsers.add_parser('sync-exports', help='Auto-generate __init__.py exports')
    init_parser.add_argument('path', help='Path to package directory')
    init_parser.add_argument('--absolute', action='store_true', default=True, help='Use absolute imports (default)')
    init_parser.add_argument('--relative', action='store_true', help='Use relative imports')
    init_parser.set_defaults(func=sync_exports)

    # Refactor Imports
    refactor_parser = dev_subparsers.add_parser('refactor-imports', help='Refactor imports to absolute or relative')
    refactor_parser.add_argument('path', nargs='?', default='src', help='Directory to refactor (default: src)')
    refactor_parser.add_argument('--to-relative', action='store_true', help='Convert absolute imports to relative')
    refactor_parser.add_argument('--to-absolute', action='store_true', help='Convert relative imports to absolute')
    refactor_parser.set_defaults(func=refactor_imports)
