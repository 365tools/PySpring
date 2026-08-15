"""
快速修复已生成的 py-demo 项目

用途：修复使用旧模板生成的项目中的 CustomUser 导入错误
"""
import os
import sys


def fix_existing_project(project_path):
    """修复已存在的项目"""

    if not os.path.exists(project_path):
        print(f"❌ 项目不存在: {project_path}")
        return False

    print("=" * 70)
    print(f"修复项目: {project_path}")
    print("=" * 70)

    files_to_fix = [
        "app/services/custom_login_provider.py",
        "app/services/custom_register_service.py"
    ]

    fixed_count = 0

    for file_path in files_to_fix:
        full_path = os.path.join(project_path, file_path)

        if not os.path.exists(full_path):
            print(f"⚠️  跳过不存在的文件: {file_path}")
            continue

        print(f"\n📝 修复文件: {file_path}")

        # 读取文件
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 执行替换
        original_content = content

        # 1. 修复 CustomUser 导入
        content = content.replace(
            'from app.config.security_config import CustomUser',
            'from app.models.user import User'
        )
        content = content.replace('CustomUser', 'User')

        # 2. 修复装饰器导入路径（注解包重构）
        content = content.replace(
            'from pyspring.core.ioc.annotations.component import',
            'from pyspring.core.ioc.annotations import'
        )
        content = content.replace(
            'from pyspring.core.ioc.annotations.configuration import',
            'from pyspring.core.ioc.annotations import'
        )
        content = content.replace(
            'from pyspring.core.ioc.annotations.modifiers import',
            'from pyspring.core.ioc.annotations import'
        )
        content = content.replace(
            'from pyspring.core.ioc.annotations.conditional import',
            'from pyspring.core.ioc.annotations import'
        )

        # 如果有修改，写回文件
        if content != original_content:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   ✅ 已修复")
            fixed_count += 1
        else:
            print(f"   ℹ️  无需修复（已是正确的）")

    print("\n" + "=" * 70)
    if fixed_count > 0:
        print(f"✅ 成功修复 {fixed_count} 个文件")
        print("\n现在可以运行项目：")
        print(f"   cd {project_path}")
        print("   pyspring run")
    else:
        print("ℹ️  没有需要修复的文件（可能已经修复过或使用新模板生成）")

    return True


if __name__ == "__main__":
    # 默认路径
    default_path = r"D:\Project\PycharmProjects\py-demo"

    # 如果命令行提供了路径，使用命令行参数
    project_path = sys.argv[1] if len(sys.argv) > 1 else default_path

    print(f"使用项目路径: {project_path}")
    print("(可以通过命令行参数指定其他路径: python fix_existing_project.py <项目路径>)\n")

    success = fix_existing_project(project_path)
    sys.exit(0 if success else 1)
