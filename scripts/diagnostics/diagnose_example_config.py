"""
PySpring Example Project 配置检查和修复脚本

用途：
1. 检查 example 项目是否正确配置了 SecurityEntityConfiguration
2. 如果缺失，自动创建配置文件
3. 验证配置是否生效

使用：
    python diagnose_example_config.py
    python diagnose_example_config.py --fix
    python diagnose_example_config.py --target /path/to/your/project
"""
import argparse
import sys
from pathlib import Path
from textwrap import dedent


def print_status(message, status="INFO"):
    """打印状态信息"""
    colors = {
        "INFO": "\033[94m",  # Blue
        "SUCCESS": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "ENDC": "\033[0m",  # Reset
    }
    color = colors.get(status, colors["INFO"])
    print(f"{color}[{status}]{colors['ENDC']} {message}")


def check_file_exists(file_path: Path) -> bool:
    """检查文件是否存在"""
    exists = file_path.exists()
    if exists:
        print_status(f"✅ 文件存在: {file_path.relative_to(file_path.parent.parent.parent)}", "SUCCESS")
    else:
        print_status(f"❌ 文件缺失: {file_path.relative_to(file_path.parent.parent.parent)}", "ERROR")
    return exists


def check_file_content(file_path: Path, pattern: str, description: str) -> bool:
    """检查文件内容是否包含特定模式"""
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding='utf-8')
    found = pattern in content

    if found:
        print_status(f"✅ {description}", "SUCCESS")
    else:
        print_status(f"❌ {description}", "ERROR")

    return found


def diagnose_example_project(project_dir: Path) -> dict:
    """诊断 example 项目配置"""
    print("\n" + "=" * 80)
    print("PySpring Example Project 配置诊断")
    print("=" * 80 + "\n")

    print_status(f"项目目录: {project_dir.absolute()}", "INFO")

    results = {
        "project_exists": False,
        "main_exists": False,
        "user_model_exists": False,
        "security_config_exists": False,
        "has_component_decorator": False,
        "has_user_orm_model": False,
        "base_packages_correct": False,
        "issues": []
    }

    # 1. 检查项目结构
    print("\n📁 检查 1/6: 项目结构")
    app_dir = project_dir / "app"
    results["project_exists"] = app_dir.exists()

    if not results["project_exists"]:
        print_status("❌ 项目目录不存在，这不是一个有效的 PySpring 项目", "ERROR")
        results["issues"].append("项目目录 'app' 不存在")
        return results

    print_status(f"✅ 项目目录存在: {app_dir}", "SUCCESS")

    # 2. 检查 main.py
    print("\n📄 检查 2/6: main.py 入口文件")
    main_file = app_dir / "main.py"
    results["main_exists"] = check_file_exists(main_file)

    if results["main_exists"]:
        results["base_packages_correct"] = check_file_content(
            main_file,
            "base_packages=['app']",
            "base_packages 包含 'app'（会扫描 app.config.security_config）"
        )
        if not results["base_packages_correct"]:
            results["issues"].append("main.py 中 base_packages 未包含 'app'")
    else:
        results["issues"].append("main.py 不存在")

    # 3. 检查 User 模型
    print("\n👤 检查 3/6: 自定义 User 模型")
    user_model_file = app_dir / "models" / "user.py"
    results["user_model_exists"] = check_file_exists(user_model_file)

    if results["user_model_exists"]:
        has_basetable = check_file_content(
            user_model_file,
            "BaseUserTable",
            "User 继承自 BaseUserTable"
        )
        has_tablename = check_file_content(
            user_model_file,
            "__tablename__",
            "User 定义了自定义表名"
        )

        if not has_basetable:
            results["issues"].append("User 模型未继承 BaseUserTable")
        if not has_tablename:
            results["issues"].append("User 模型未定义 __tablename__")
    else:
        results["issues"].append("app/models/user.py 不存在")

    # 4. 检查 security_config.py（核心）
    print("\n🔐 检查 4/6: 安全配置文件（核心）")
    security_config_file = app_dir / "config" / "security_config.py"
    results["security_config_exists"] = check_file_exists(security_config_file)

    if results["security_config_exists"]:
        results["has_component_decorator"] = check_file_content(
            security_config_file,
            "@Component",
            "CustomSecurityEntityConfiguration 有 @Component 装饰器"
        )
        results["has_user_orm_model"] = check_file_content(
            security_config_file,
            "self.user_orm_model = User",
            "配置了自定义 user_orm_model"
        )

        if not results["has_component_decorator"]:
            results["issues"].append("security_config.py 缺少 @Component 装饰器")
        if not results["has_user_orm_model"]:
            results["issues"].append("security_config.py 未配置 self.user_orm_model = User")
    else:
        results["issues"].append("app/config/security_config.py 不存在（关键文件！）")

    # 5. 检查 config/security.yaml
    print("\n⚙️  检查 5/6: 配置文件")
    security_yaml = project_dir / "config" / "security.yaml"
    if check_file_exists(security_yaml):
        check_file_content(
            security_yaml,
            "identifier_fields",
            "security.yaml 包含 identifier_fields 配置"
        )

    # 6. 总结
    print("\n📊 检查 6/6: 诊断总结")

    all_checks_passed = (
            results["project_exists"] and
            results["main_exists"] and
            results["user_model_exists"] and
            results["security_config_exists"] and
            results["has_component_decorator"] and
            results["has_user_orm_model"] and
            results["base_packages_correct"]
    )

    if all_checks_passed:
        print_status("🎉 所有检查通过！配置正确。", "SUCCESS")
    else:
        print_status(f"⚠️  发现 {len(results['issues'])} 个问题", "WARNING")
        for i, issue in enumerate(results["issues"], 1):
            print(f"  {i}. {issue}")

    return results


def create_security_config_file(project_dir: Path) -> bool:
    """创建 security_config.py 文件"""
    config_dir = project_dir / "app" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)

    security_config_file = config_dir / "security_config.py"

    if security_config_file.exists():
        print_status(f"文件已存在，跳过: {security_config_file}", "WARNING")
        return False

    content = dedent('''
        """
        PySpring 安全模块自定义配置
        
        用途：
        - 告诉框架使用自定义的 User 模型（而不是默认的 UserTable）
        - 这样 identifier 登录才能查询正确的用户表
        
        重要：
        - 必须有 @Component 装饰器
        - 必须继承 SecurityEntityConfiguration
        - 重写 user_orm_model 指向你的自定义 User 类
        """
        from pyspring.core.ioc.annotations import Component
        from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
        from app.models.user import User  # 导入自定义 User 模型
        
        
        @Component
        class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
            """自定义安全实体配置"""
            
            def __init__(self):
                super().__init__()  # 继承所有默认值
                
                # 只重写需要自定义的字段
                self.user_orm_model = User  # ✅ 使用自定义的 User 模型
                
                # 其他字段（role_orm_model, permission_orm_model 等）自动继承默认值
                # 无需显式声明！
    ''').strip()

    security_config_file.write_text(content, encoding='utf-8')
    print_status(f"✅ 已创建: {security_config_file}", "SUCCESS")

    return True


def fix_example_project(project_dir: Path, results: dict):
    """修复 example 项目配置"""
    print("\n" + "=" * 80)
    print("🔧 自动修复")
    print("=" * 80 + "\n")

    fixed_count = 0

    # 修复 1: 创建 security_config.py
    if not results["security_config_exists"]:
        print_status("正在创建 app/config/security_config.py...", "INFO")
        if create_security_config_file(project_dir):
            fixed_count += 1

    # 修复 2: 其他问题需要手动处理
    manual_fixes = []

    if not results["user_model_exists"]:
        manual_fixes.append("创建 app/models/user.py（继承 BaseUserTable）")

    if not results["base_packages_correct"]:
        manual_fixes.append("修改 app/main.py，确保 base_packages=['app']")

    if manual_fixes:
        print("\n⚠️  以下问题需要手动修复：")
        for i, fix in enumerate(manual_fixes, 1):
            print(f"  {i}. {fix}")

    if fixed_count > 0:
        print_status(f"\n✅ 已修复 {fixed_count} 个问题", "SUCCESS")
        print("\n请重启应用以使配置生效：")
        print("  uvicorn app.main:app --reload")
    else:
        print_status("\n没有可自动修复的问题", "INFO")


def main():
    parser = argparse.ArgumentParser(description="PySpring Example Project 配置诊断和修复")
    parser.add_argument(
        "--target",
        type=str,
        default=".",
        help="项目目录路径（默认：当前目录）"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复发现的问题"
    )

    args = parser.parse_args()

    project_dir = Path(args.target).resolve()

    # 诊断
    results = diagnose_example_project(project_dir)

    # 修复
    if args.fix and results["issues"]:
        fix_example_project(project_dir, results)
    elif results["issues"] and not args.fix:
        print("\n" + "=" * 80)
        print("💡 提示：运行以下命令自动修复部分问题：")
        print(f"  python {Path(__file__).name} --fix")
        print("=" * 80)

    # 退出码
    sys.exit(0 if not results["issues"] else 1)


if __name__ == "__main__":
    main()
