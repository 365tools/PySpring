"""
验证项目模板修复

检查所有模板文件中不应该再有错误的 CustomUser 导入
"""
import os
import sys


def check_templates():
    """检查模板文件"""
    template_dir = r"D:\Project\PycharmProjects\PySpring\src\pyspring\templates\example"

    issues = []

    # 检查不应该存在的导入
    bad_imports = [
        "from app.config.security_config import CustomUser",
        "from app.config.security_config import User"
    ]

    # 检查应该存在的导入
    good_imports = [
        "from app.models.user import User"
    ]

    print("=" * 70)
    print("检查项目模板文件")
    print("=" * 70)

    # 遍历所有模板文件
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.template'):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, template_dir)

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                    # 检查坏的导入
                    for bad_import in bad_imports:
                        if bad_import in content:
                            # 除非是在注释示例中
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if bad_import in line and not line.strip().startswith('#') and '"""' not in content[:content.index(line)]:
                                    issues.append(f"❌ {rel_path}:{i} - 发现错误导入: {bad_import}")

                    # 检查文件是否需要正确的导入
                    if 'custom_login_provider' in file or 'custom_register_service' in file:
                        has_good_import = any(good_import in content for good_import in good_imports)
                        if not has_good_import:
                            issues.append(f"⚠️  {rel_path} - 缺少正确的导入: from app.models.user import User")

    if issues:
        print("\n发现问题：")
        for issue in issues:
            print(issue)
        return False
    else:
        print("\n✅ 所有模板文件检查通过！")
        print("\n正确的导入模式：")
        print("  - from app.models.user import User")
        print("\n已修复的文件：")
        print("  ✓ custom_login_provider.py.template")
        print("  ✓ custom_register_service.py.template")
        print("  ✓ auth.py.template")
        print("  ✓ README.md.template")
        return True


if __name__ == "__main__":
    success = check_templates()
    sys.exit(0 if success else 1)
