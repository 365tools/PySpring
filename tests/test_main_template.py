"""测试从模板创建 main.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import tempfile
from pyspring.cli.tools.init import create_main_file, get_template_dir

# 检查模板文件
print("=" * 80)
print("检查模板文件")
print("=" * 80)
template_dir = get_template_dir()
main_template = template_dir / "main.py.template"
print(f"模板路径: {main_template}")
print(f"模板存在: {main_template.exists()}")
if main_template.exists():
    size = main_template.stat().st_size
    print(f"模板大小: {size} bytes")

# 创建临时目录
temp_dir = Path(tempfile.mkdtemp())
print(f"\n测试目录: {temp_dir}\n")

# 创建 main.py
print("=" * 80)
print("创建 main.py")
print("=" * 80)
create_main_file(temp_dir)

# 验证
main_path = temp_dir / "main.py"
if main_path.exists():
    content = main_path.read_text(encoding='utf-8')
    lines = content.split('\n')
    print(f"\n✓ 生成的 main.py ({len(lines)} 行, {len(content)} 字符)")
    print(f"\n前 30 行:")
    print("-" * 80)
    for i, line in enumerate(lines[:30], 1):
        print(f"{i:3d}: {line}")
    print("\n..." if len(lines) > 30 else "")

print("\n" + "=" * 80)
print("✅ 测试完成！")
print("=" * 80)
