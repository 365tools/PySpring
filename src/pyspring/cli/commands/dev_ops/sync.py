"""
模板文件同步脚本

用于将 PySpring 根目录的配置文件同步到 templates 目录
"""
import shutil
from pathlib import Path

from pyspring.cli.core.ui import (
    print_title, print_error, print_info, print_issue, print_summary
)


def sync_templates(args):
    """同步模板文件"""
    current_file = Path(__file__)
    # Resolve root from this file location: src/pyspring/cli/commands/dev_ops/sync.py
    # Root is 6 levels up
    root = current_file.parent.parent.parent.parent.parent.parent

    # If installed as package usage, this might fail to find root if not editable
    if not (root / "pyproject.toml").exists():
        # Fallback try assuming CWD is root
        root = Path.cwd()
        if not (root / "pyproject.toml").exists():
            print_error("Could not search project root. Please run from project root directory.")
            return

    templates_dir = root / "src" / "pyspring" / "templates" / "project"

    # 确保模板目录存在
    templates_dir.mkdir(parents=True, exist_ok=True)

    # 要同步的文件
    files_to_sync = [
        (".gitignore", ".gitignore.template"),
        ("pyproject.toml", "pyproject.toml.template"),
        ("examples/main_with_db_init.py", "main.py.template"),
    ]

    print_title("同步模板文件到 templates 目录")

    synced_count = 0
    issues_count = 0

    for source_name, target_name in files_to_sync:
        source_path = root / source_name
        target_path = templates_dir / target_name

        if not source_path.exists():
            print_issue("0", f"源文件不存在: {source_name}", level='error')
            issues_count += 1
            continue

        # 复制文件
        try:
            shutil.copy2(source_path, target_path)

            # 获取文件大小
            size = target_path.stat().st_size
            print_issue("1", f"{source_name} → {target_name} ({size:,} bytes)", str(target_path), level='success')
            synced_count += 1
        except Exception as e:
            print_issue("0", f"同步失败: {e}", str(target_path), level='error')
            issues_count += 1

    print_info(f"模板目录: {templates_dir}")
    print_info("可用模板文件:")
    for file_path in sorted(templates_dir.glob("*")):
        if file_path.is_file():
            print(f"  - {file_path.name}")

    print_summary(issues_count, 0, synced_count, fixable=False)
