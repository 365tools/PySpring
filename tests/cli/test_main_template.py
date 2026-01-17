"""测试从模板创建 main.py"""
import sys
import tempfile
from pathlib import Path

# Ensure src is in path for imports
PROJ_ROOT = Path(__file__).parent.parent.parent
if str(PROJ_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJ_ROOT / "src"))

from pyspring.cli.commands.init_ops.core import create_main_file, get_template_dir


def test_create_main_file_from_template():
    """验证从模板生成 main.py 的功能"""
    # 检查模板文件
    print("=" * 80)
    print("检查模板文件")
    print("=" * 80)
    template_dir = get_template_dir()
    main_template = template_dir / "main.py.template"
    print(f"模板路径: {main_template}")

    assert main_template.exists(), f"Template not found at {main_template}"
    
    size = main_template.stat().st_size
    print(f"模板大小: {size} bytes")

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print(f"\n测试目录: {temp_dir}\n")

        # 创建 main.py
        print("=" * 80)
        print("创建 main.py")
        print("=" * 80)
        create_main_file(temp_dir)

        # 验证
        main_path = temp_dir / "main.py"
        assert main_path.exists(), "main.py was not created"

        content = main_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        print(f"\n✓ 生成的 main.py ({len(lines)} 行, {len(content)} 字符)")

        assert len(lines) > 0, "Generated main.py is empty"
        assert "FastAPI" in content, "Generated content missing expected keywords"

        print(f"\n前 30 行:")
        print("-" * 80)
        for i, line in enumerate(lines[:30], 1):
            print(f"{i:3d}: {line}")
        print("\n..." if len(lines) > 30 else "")

    print("\n" + "=" * 80)
    print("✅ 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_create_main_file_from_template()
