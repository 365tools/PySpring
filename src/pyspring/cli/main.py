"""
PySpring CLI 主程序入口
"""
import sys

from .tools.diagnose import main as diagnose_main
from .tools.init import main as init_main
from .tools.uv_manager import main as uv_main


def main():
    """CLI 主入口"""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'init':
            # 移除 'init' 参数，让 init.py 的 argparse 处理剩余参数
            sys.argv.pop(1)
            init_main()
        elif command == 'diagnose':
            # 运行诊断命令
            diagnose_main()
        elif command == 'uv':
            # 运行 uv 管理命令（不移除参数，让 uv_manager 处理）
            uv_main()
        else:
            print(f"错误: 未知命令 '{command}'\n")
            print_help()
    else:
        print_help()


def print_help():
    """打印帮助信息"""
    print("""
PySpring 框架命令行工具

用法:
  pyspring <command> [options]

可用命令:
  init          初始化 PySpring 项目配置
  diagnose      诊断 PySpring 导入和安装问题
  uv            管理 uv 虚拟环境
  
示例:
  # 初始化当前目录
  pyspring init
  
  # 初始化指定目录
  pyspring init /path/to/project
  
  # 查看 init 命令帮助
  pyspring init --help
  
  # 诊断安装问题
  pyspring diagnose
  
  # uv 环境管理
  pyspring uv setup
  pyspring uv status
  pyspring uv help

获取更多信息:
  https://github.com/365tools/PySpring
    """)


if __name__ == "__main__":
    main()
