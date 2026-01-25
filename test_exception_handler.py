"""
测试异常处理器的项目根路径解析
"""
from pathlib import Path

from pyspring.web.handlers.exception import GlobalExceptionHandler

# 测试项目根路径解析
print("=" * 80)
print("测试项目根路径解析")
print("=" * 80)

project_root = GlobalExceptionHandler._project_root()
print(f"项目根路径: {project_root}")
print(f"当前工作目录: {Path.cwd()}")

# 测试相对路径转换
print("\n" + "=" * 80)
print("测试相对路径转换")
print("=" * 80)

test_paths = [
    str(Path.cwd() / "src" / "pyspring" / "web" / "handlers" / "exception.py"),  # 项目内文件
    str(Path.cwd() / ".venv" / "Lib" / "site-packages" / "fastapi" / "routing.py"),  # 虚拟环境
    "D:\\Python\\Lib\\json\\__init__.py",  # 系统库
]

for path in test_paths:
    rel_path = GlobalExceptionHandler._relpath(path)
    print(f"\n原始路径: {path}")
    print(f"转换结果: {rel_path}")
    print(f"是相对路径: {not Path(rel_path).is_absolute()}")
