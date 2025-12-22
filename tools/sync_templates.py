"""
模板文件同步脚本

用于将 PySpring 根目录的配置文件同步到 templates 目录
"""
import shutil
from pathlib import Path


def sync_templates():
    """同步模板文件"""
    root = Path(__file__).parent.parent
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
            size = file_path.stat().st_size
            print(f"  - {file_path.name:40} ({size:>6,} bytes)")


if __name__ == "__main__":
    sync_templates()
