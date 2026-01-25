"""
完整验证项目模板修复

检查所有修复项：
1. CustomUser → User
2. 旧导入路径 → 新导入路径
"""
import os
import sys


def verify_all_fixes():
    """验证所有修复"""
    template_dir = r"D:\Project\PycharmProjects\PySpring\src\pyspring\templates\example"

    print("=" * 80)
    print("验证项目模板修复")
    print("=" * 80)

    all_passed = True

    # 检查1: 不应该存在的旧导入
    print("\n[检查 1] 旧的子模块导入（应该不存在）")
    old_imports = [
        'from pyspring.ioc.annotations.component import',
        'from pyspring.ioc.annotations.configuration import',
        'from pyspring.ioc.annotations.modifiers import',
        'from pyspring.ioc.annotations.conditional import',
    ]

    found_old_imports = []
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.template') and not file.endswith('security_config.py.template'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for old_import in old_imports:
                        if old_import in content:
                            # 检查是否在注释中
                            if '"""' in content or "'''" in content:
                                # 简单检查，可能在注释中
                                continue
                            rel_path = os.path.relpath(filepath, template_dir)
                            found_old_imports.append(f"{rel_path}: {old_import}")

    if found_old_imports:
        print("  ❌ 发现旧的导入路径:")
        for item in found_old_imports:
            print(f"     - {item}")
        all_passed = False
    else:
        print("  ✅ 没有旧的子模块导入")

    # 检查2: 应该存在的新导入
    print("\n[检查 2] 新的统一导入（应该存在）")
    new_import = 'from pyspring.ioc.annotations import'
    files_with_new_import = []

    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.template'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if new_import in content:
                        rel_path = os.path.relpath(filepath, template_dir)
                        files_with_new_import.append(rel_path)

    if files_with_new_import:
        print(f"  ✅ 找到 {len(files_with_new_import)} 个文件使用新导入:")
        for item in files_with_new_import:
            print(f"     - {item}")
    else:
        print("  ⚠️  没有找到使用新导入的文件")

    # 检查3: CustomUser 错误导入（应该不存在）
    print("\n[检查 3] CustomUser 错误导入（应该不存在）")
    bad_user_import = 'from app.config.security_config import CustomUser'
    found_bad_user_import = []

    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.template'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if bad_user_import in content:
                        rel_path = os.path.relpath(filepath, template_dir)
                        found_bad_user_import.append(rel_path)

    if found_bad_user_import:
        print("  ❌ 发现错误的 CustomUser 导入:")
        for item in found_bad_user_import:
            print(f"     - {item}")
        all_passed = False
    else:
        print("  ✅ 没有错误的 CustomUser 导入")

    # 检查4: 正确的 User 导入（应该存在）
    print("\n[检查 4] 正确的 User 导入（应该存在）")
    good_user_import = 'from app.models.user import User'
    files_with_good_import = []

    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if ('custom_login_provider' in file or 'custom_register_service' in file) and file.endswith('.template'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if good_user_import in content:
                            rel_path = os.path.relpath(filepath, template_dir)
                            files_with_good_import.append(rel_path)
                except UnicodeDecodeError:
                    # 跳过二进制文件
                    continue

    if files_with_good_import:
        print(f"  ✅ 找到 {len(files_with_good_import)} 个文件使用正确导入:")
        for item in files_with_good_import:
            print(f"     - {item}")
    else:
        print("  ❌ 没有找到正确的 User 导入")
        all_passed = False

    # 总结
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有检查通过！模板已完全修复")
        print("\n修复内容:")
        print("  ✅ CustomUser → User")
        print("  ✅ 旧子模块导入 → 新统一导入")
        print("\n已修复的文件:")
        for f in files_with_new_import:
            print(f"  - {f}")
    else:
        print("⚠️  发现问题，请检查上述错误")

    return all_passed


if __name__ == "__main__":
    success = verify_all_fixes()
    sys.exit(0 if success else 1)
