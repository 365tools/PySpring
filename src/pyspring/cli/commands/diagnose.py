"""
PySpring Diagnose Command
"""
from .diagnose_ops.core import run


def register_subcommand(subparsers):
    """注册 diagnose 子命令"""
    parser = subparsers.add_parser(
        'diagnose',
        help='Diagnose PySpring installation and import issues',
        description='Diagnose PySpring installation and import issues'
    )
    parser.set_defaults(func=run)
