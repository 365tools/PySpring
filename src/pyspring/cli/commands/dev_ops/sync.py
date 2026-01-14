"""
模板文件同步脚本

用于将 PySpring 根目录的配置文件同步到 templates 目录
"""
import shutil
from pathlib import Path


def sync_templates(args):
    """同步模板文件"""
    # Assuming this is run from within the installed package or src
    # We need to find the project root if running from source.
    # Current file: src/pyspring/cli/commands/dev_ops/sync.py
    # Root: ../../../../../

    # However, if installed, we might not have access to source root files like .gitignore
    # This command is typically run by developers working ON PySpring framework itself

    current_file = Path(__file__)
    # src/pyspring/cli/commands/dev_ops/sync.py
    # src/pyspring/cli/commands/dev_ops
    # src/pyspring/cli/commands
    # src/pyspring/cli
    # src/pyspring
    # src
    # root
    root = current_file.parent.parent.parent.parent.parent.parent

    # If installed as package usage, this might fail to find root if not editable
    if not (root / "pyproject.toml").exists():
        # Fallback try assuming CWD is root
        root = Path.cwd()
        if not (root / "pyproject.toml").exists():
            print("❌ Could not search project root. Please run from project root directory.")
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

    print("=" * 80)
    print("同步模板文件到 templates 目录")
    print("=" * 80)

    for source_name, target_name in files_to_sync:
        source_path = root / source_name
        target_path = templates_dir / target_name

        if not source_path.exists():
            print(f"✗ 源文件不存在: {source_path}")
            continue

        # 复制文件
        shutil.copy2(source_path, target_path)

        # 获取文件大小
        size = target_path.stat().st_size
        print(f"✓ {source_name:30} → {target_name:30} ({size:,} bytes)")

    print("\n" + "=" * 80)
    print("✅ 模板文件同步完成！")
    print("=" * 80)
    print(f"模板目录: {templates_dir}")
    print("\n可用模板文件:")
    for file_path in sorted(templates_dir.glob("*")):
        if file_path.is_file():
            print(f"- {file_path.name}")
