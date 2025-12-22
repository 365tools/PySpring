"""
批量更新所有 __init__.py 文件
"""
from pathlib import Path

INIT_TEMPLATE = '''"""
自动导入模块
"""
from utils.auto_import import auto_import_package

# 执行自动导入
_exported_items = auto_import_package(__name__)

# 更新全局命名空间
globals().update(_exported_items)

# 生成 __all__
__all__ = sorted(list(_exported_items.keys()))
'''


def update_all_init_files():
    """更新所有 __init__.py 文件"""
    project_root = Path(__file__).parent.parent

    # 需要手动维护的 __init__.py（不自动更新）
    skip_paths = [
        "pyspring/__init__.py",  # 根模块，手动导出
        "pyspring/cli/__init__.py",  # CLI 入口，手动导出
        "pyspring/cli/tools/__init__.py",  # CLI 工具模块
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
