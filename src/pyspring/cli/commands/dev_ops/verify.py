"""验证生成的 pyproject.toml 完整内容"""
import shutil
import tempfile
from pathlib import Path

# Correct import path assuming internal usage
from pyspring.cli.commands.init_ops.core import create_pyproject_toml


def verify_pyproject(args):
    """验证 pyproject.toml 生成逻辑"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        create_pyproject_toml(temp_dir)

        pyproject_path = temp_dir / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding='utf-8')

            print("=" * 80)
            print("完整的 pyproject.toml 内容:")
            print("=" * 80)
            print(content)
            print("=" * 80)
        else:
            print("❌ Failed to generate pyproject.toml")
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
