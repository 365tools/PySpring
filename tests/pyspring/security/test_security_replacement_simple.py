# -*- coding: utf-8 -*-
"""
简化测试：直接验证替换机制

不依赖包扫描，直接手动注册来验证逻辑
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import Column, String
from pyspring.repositories.db.models.common.define import BaseUserTable
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.orm.tables import UserTable


# 自定义 User 模型
class CustomUser(BaseUserTable):
    __tablename__ = "custom_users"
    username = Column(String(50), unique=True)
    phone = Column(String(20))


def test_direct_replacement():
    """直接测试：手动创建配置实例"""
    print("=" * 80)
    print("测试：直接创建自定义配置实例")
    print("=" * 80 + "\n")

    # 1. 框架默认配置
    print("1️⃣ 框架默认配置:")
    default_config = SecurityEntityConfiguration()
    print(f"   user_orm_model: {default_config.user_orm_model}")
    print(f"   表名: {default_config.user_orm_model.__tablename__}\n")

    # 2. 自定义配置（模拟 example 的做法）
    print("2️⃣ 自定义配置 (模拟 example):")

    class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
        def __init__(self):
            super().__init__()
            self.user_orm_model = CustomUser  # 重写

    custom_config = CustomSecurityEntityConfiguration()
    print(f"   user_orm_model: {custom_config.user_orm_model}")
    print(f"   表名: {custom_config.user_orm_model.__tablename__}\n")

    # 3. 验证
    print("3️⃣ 验证结果:")
    checks = [
        ("自定义配置是 SecurityEntityConfiguration 的子类", isinstance(custom_config, SecurityEntityConfiguration)),
        ("user_orm_model 是 CustomUser", custom_config.user_orm_model == CustomUser),
        ("不是默认的 UserTable", custom_config.user_orm_model != UserTable),
        ("表名是 custom_users", custom_config.user_orm_model.__tablename__ == "custom_users"),
    ]

    all_passed = True
    for desc, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {desc}")
        if not result:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 直接实例化测试通过！配置继承机制正常工作！")
    else:
        print("❌ 测试失败")
    print("=" * 80 + "\n")

    return all_passed


def test_ioc_registration():
    """测试IoC容器注册"""
    print("=" * 80)
    print("测试：IoC 容器中的Bean名称机制")
    print("=" * 80 + "\n")

    print("分析：@Component 如何生成 Bean 名称...\n")

    # 模拟 _generate_name 逻辑
    import re
    def generate_name(cls: type) -> str:
        name = cls.__name__
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    from pyspring.ioc.annotations import Component

    @Component
    class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
        def __init__(self):
            super().__init__()
            self.user_orm_model = CustomUser

    parent_name = generate_name(SecurityEntityConfiguration)
    child_name = generate_name(CustomSecurityEntityConfiguration)

    print(f"父类 SecurityEntityConfiguration Bean名称: '{parent_name}'")
    print(f"子类 CustomSecurityEntityConfiguration Bean名称: '{child_name}'")
    print()

    if parent_name == child_name:
        print("✅ 父类和子类使用相同的 Bean 名称！")
        print("   应该会发生替换（如果后注册）\n")
        return True
    else:
        print("❌ 问题：父类和子类使用不同的 Bean 名称！")
        print(f"   - 父类：'{parent_name}'")
        print(f"   - 子类：'{child_name}'")
        print("   这意味着不会发生替换！\n")
        print("💡 解决方案：")
        print("   方案1：手动指定相同的 Bean 名称")
        print("          @Component(name='security_entity_configuration')")
        print()
        print("   方案2：注册时检测继承关系")
        print("          如果子类继承父类且父类有 @ConditionalOnMissingBean")
        print("          则用子类替换父类")
        return False


if __name__ == "__main__":
    print("\n🔬 PySpring SecurityEntityConfiguration 替换机制测试\n")

    # 测试1：直接实例化
    test1 = test_direct_replacement()

    # 测试2：IoC注册机制
    test2 = test_ioc_registration()

    print("\n" + "=" * 80)
    print("📊 总结")
    print("=" * 80)
    print(f"直接实例化测试: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"IoC Bean名称测试: {'✅ 通过' if test2 else '❌ 失败'}")
    print("=" * 80)
