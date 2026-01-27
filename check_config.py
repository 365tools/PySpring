import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / 'src'))

from pyspring.config.manager import ConfigManager

cfg = ConfigManager()
console_format = cfg.get('logging', {}).get('console', {}).get('format')
print("控制台格式:")
print(console_format)
print()
print("是否包含 file_relative:", "file_relative" in str(console_format))
print("是否包含 File:", "File" in str(console_format))
