"""
框架完整性验证脚本

验证所有核心文件的语法和导入
"""
import os
import sys

# 获取脚本所在目录（框架根目录）
FRAMEWORK_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(FRAMEWORK_ROOT, 'src'))


def test_syntax():
    """测试语法"""
    import ast

    files = [
        'src/pyspring/web/handlers/exception.py',
        'src/pyspring/web/handlers/base.py',
        'src/pyspring/ioc/context.py',
        'src/pyspring/security/authentication/token/service.py',
        'src/pyspring/security/authentication/factories/auth_provider/factory.py',
    ]

    print("=" * 80)
    print("📝 验证语法...")
    print("=" * 80)

    for file in files:
        file_path = os.path.join(FRAMEWORK_ROOT, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            print(f"✅ {file}")
        except SyntaxError as e:
            print(f"❌ {file}: {e}")
            return False

    return True


def test_imports():
    """测试导入"""
    print("\n" + "=" * 80)
    print("📦 验证导入...")
    print("=" * 80)

    try:
        from pyspring.web.handlers.base import IExceptionHandler
        print("✅ IExceptionHandler")

        from pyspring.web.handlers.exception import GlobalExceptionHandler
        print("✅ GlobalExceptionHandler")

        from pyspring.ioc import ApplicationContext
        print("✅ ApplicationContext")

        # 验证继承关系
        assert issubclass(GlobalExceptionHandler, IExceptionHandler), "GlobalExceptionHandler 必须实现 IExceptionHandler"
        print("✅ GlobalExceptionHandler 实现了 IExceptionHandler")

        # 验证装饰器
        assert hasattr(GlobalExceptionHandler, '__pyspring_component__'), "GlobalExceptionHandler 必须有 @Component 装饰器"
        print("✅ GlobalExceptionHandler 已注册为 IoC 组件")

        return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_syntax():
    """测试模板语法"""
    import ast

    print("\n" + "=" * 80)
    print("📄 验证模板文件...")
    print("=" * 80)

    templates = [
        'src/pyspring/templates/example/app/main.py.template',
        'src/pyspring/templates/example/app/config/security_config.py.template',
        'src/pyspring/templates/example/app/database/initializer.py.template',
        'src/pyspring/templates/example/app/services/auth_service.py.template',
    ]

    for file in templates:
        file_path = os.path.join(FRAMEWORK_ROOT, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            print(f"✅ {os.path.basename(file)}")
        except SyntaxError as e:
            print(f"❌ {os.path.basename(file)}: {e}")
            return False

    return True


def main():
    print("\n🚀 PySpring 框架完整性验证\n")

    success = True
    success = test_syntax() and success
    success = test_imports() and success
    success = test_template_syntax() and success

    print("\n" + "=" * 80)
    if success:
        print("✅ 所有验证通过！框架完整性正常")
    else:
        print("❌ 验证失败！请检查错误信息")
    print("=" * 80 + "\n")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
