"""验证生成的 pyproject.toml 完整内容"""
import tempfile
from pathlib import Path

from src.pyspring.init import create_pyproject_toml

temp_dir = Path(tempfile.mkdtemp())
create_pyproject_toml(temp_dir)

pyproject_path = temp_dir / "pyproject.toml"
content = pyproject_path.read_text(encoding='utf-8')

print("=" * 80)
print("完整的 pyproject.toml 内容:")
print("=" * 80)
print(content)
print("=" * 80)
