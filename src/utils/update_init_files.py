"""
批量更新所有 __init__.py 文件
"""
from pathlib import Path

INIT_TEMPLATE = '''"""
自动导入模块
"""
from utils.auto_import import auto_import_package

__all__ = auto_import_package(__name__, globals())
'''


def update_all_init_files():
    """更新所有 __init__.py 文件"""
    project_root = Path(__file__).parent.parent

    # 需要手动维护的 __init__.py（不自动更新）
    # 这里维护白名单，防止 update_init_files.py 脚本覆盖了手动修改的特殊逻辑
    skip_paths = [
        "pyspring/__init__.py",  # 根模块：手动控制导出，防止 import pyspring 时触发全量加载（如日志、安全模块）
        "pyspring/cli/__init__.py",  # CLI 入口：防止 CLI 启动时自动导入所有子命令，保持启动轻量
        "pyspring/cli/tools/__init__.py",  # CLI 工具模块：特殊用途
        "pyspring/core/__init__.py",  # Core 模块：包含大量基础组件，避免 import pyspring.core 时触发如日志初始化等副作用
        "pyspring/log/__init__.py",  # Log 模块：防止 import pyspring.log 时立即配置日志，应按需加载
    ]

    # 跳过的目录
    skip_dirs = {
        "__pycache__", ".git", "venv", "env", ".venv",
        "site-packages",  # 跳过所有第三方包
        "dist", "build", "egg-info",
    }

    # 查找所有包含 Python 文件的目录
    for init_file in project_root.rglob("__init__.py"):
        # 跳过包含特殊目录的路径
        if any(skip_dir in init_file.parts for skip_dir in skip_dirs):
            continue

        # 检查是否在排除列表中
        relative_path = init_file.relative_to(project_root).as_posix()
        if any(skip_path in relative_path for skip_path in skip_paths):
            print(f"Skipped (manual): {init_file}")
            continue

        # 检查是否有其他 .py 文件
        py_files = list(init_file.parent.glob("*.py"))
        if len(py_files) > 1:  # 除了 __init__.py 还有其他文件
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(INIT_TEMPLATE.strip() + "\n")
            print(f"Updated: {init_file}")


if __name__ == "__main__":
    update_all_init_files()
    print("All __init__.py files updated!")
