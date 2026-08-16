"""
PySpring CLI Main Entry Point
"""
import io
import os
import sys

from .core.commands.loader import load_commands
from .core.parser.custom import FriendlyArgumentParser
from .core.parser.formatter import GroupedHelpFormatter


def _should_show_banner():
    """
    判断是否应该显示 Banner
    
    以下情况不显示 Banner:
    - 帮助命令 (-h, --help)
    - 版本命令 (-v, --version)
    - 特定命令 (如 init, diagnose 等需要快速响应的)
    """
    if len(sys.argv) < 2:
        return True

    # 不显示 Banner 的命令
    skip_commands = {'-h', '-v', '--version', 'init', 'diagnose', 'check', 'clean', 'uv'}

    # 检查是否是帮助或版本查询
    if sys.argv[1] in {'-h', '--help', '-v', '--version'}:
        return False

    # 检查是否是特定命令
    if sys.argv[1] in skip_commands:
        return False

    return True


def _print_banner():
    """打印 Banner"""
    try:
        # 获取 Python 版本
        import platform
        from importlib import metadata

        from ._version import __version__
        from .banner import get_banner
        python_version = platform.python_version()

        # 获取 FastAPI 版本（可选，失败则显示占位）
        try:
            fastapi_version = metadata.version('fastapi')
        except Exception:
            fastapi_version = "unknown"

        # 使用 compact 风格（紧凑且对齐完美）；version 为 CLI 自身版本
        banner = get_banner(
            style="compact",
            version=__version__,
            python_version=python_version,
            fastapi_version=fastapi_version
        )
        print(banner)
        print()
    except Exception:
        # Banner 显示失败不影响 CLI 正常使用
        pass


def main():
    """CLI Entry Point"""
    # 从源头解决 Windows GBK 控制台编码问题：
    # 统一将 stdout/stderr 配置为 UTF-8，确保任意合法 Unicode 输出不崩溃。
    # 用 isinstance 收窄为 TextIOWrapper（其 reconfigure 可安全调用），避免 try/except 吞异常。
    for _stream in (sys.stdout, sys.stderr):
        if isinstance(_stream, io.TextIOWrapper):
            _stream.reconfigure(encoding="utf-8")


    # 显示 Banner (如果环境变量未禁用)
    if _should_show_banner() and not os.getenv('PYSPRING_NO_BANNER'):
        _print_banner()

    parser = FriendlyArgumentParser(
        prog='pyspring',
        description='PySpring Framework Command Line Interface',
        epilog='For more information, visit https://github.com/365tools/PySpring',
        formatter_class=GroupedHelpFormatter
    )

    from ._version import __version__
    parser.add_argument('-v', '--version', action='version', version=f'PySpring {__version__}')
    parser.add_argument('--all', action='store_true', help='Show detailed help for all commands')

    subparsers = parser.add_subparsers(
        title='Available Commands',
        dest='command',
        required=False,
        metavar='<command>'
    )

    # Register subcommands dynamically
    load_commands(subparsers)

    # Show help if no arguments provided
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Parse arguments
    args = parser.parse_args()

    # Handle --all flag (Global Help) ONLY if no subcommand is selected
    if hasattr(args, 'all') and args.all and not args.command:
        from .core.ui.help import print_recursive_help
        print_recursive_help(parser)
        sys.exit(0)

    # If no command is selected (and not --all), show help
    if not args.command:
        parser.print_help(sys.stderr)
        sys.exit(1)

    # Execute the registered function for the subcommand
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

