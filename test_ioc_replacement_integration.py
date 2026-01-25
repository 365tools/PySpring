# -*- coding: utf-8 -*-
"""
测试重构后的 IoC 替换机制

验证两阶段扫描和类型映射是否正常工作
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import Column, String
from pyspring.ioc import ApplicationContext
from pyspring.ioc.annotations import Component
from pyspring.repositories.db.models.common.define import BaseUserTable
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration


# ============================================================
# 测试组件定义
# ============================================================

# 自定义 User 模型
class CustomUser(BaseUserTable):
    __tablename__ = "custom_users"
    username = Column(String(50), unique=True)
    phone = Column(String(20))


# 自定义配置（继承框架默认配置）
@Component()
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
    """自定义安全配置 - 测试继承替换"""

    def __init__(self):
        super().__init__()
        self.user_orm_model = CustomUser


def test_inheritance_replacement():
    """测试基于继承的替换机制"""
    print("\n" + "=" * 80)
    print("集成测试：IoC 容器继承替换机制")
    print("=" * 80 + "\n")

    print("📦 初始化 ApplicationContext...")
    print("   预期：")
    print("   1. 扫描框架的 SecurityEntityConfiguration (@ConditionalOnMissingBean)")
    print("   2. 扫描用户的 CustomSecurityEntityConfiguration (@Component)")
    print("   3. 检测到继承关系")
    print("   4. 用子类替换父类\n")

    # 初始化容器
    app_context = ApplicationContext.initialize(
        base_packages=[__name__],
        enable_aop=False
    )

    print("\n🔍 验证结果...\n")

    # 获取配置
    config = app_context.get_bean(SecurityEntityConfiguration)

    print(f"1️⃣ 获取到的 Bean 类型: {type(config).__name__}")
    print(f"   预期: CustomSecurityEntityConfiguration")
    print(f"   结果: {'✅ 正确' if type(config).__name__ == 'CustomSecurityEntityConfiguration' else '❌ 错误'}\n")

    print(f"2️⃣ user_orm_model 类型: {config.user_orm_model.__name__}")
    print(f"   预期: CustomUser")
    print(f"   结果: {'✅ 正确' if config.user_orm_model == CustomUser else '❌ 错误'}\n")

    print(f"3️⃣ 表名: {config.user_orm_model.__tablename__}")
    print(f"   预期: custom_users")
    print(f"   结果: {'✅ 正确' if config.user_orm_model.__tablename__ == 'custom_users' else '❌ 错误'}\n")

    # 验证框架默认配置未被注册
    from pyspring.ioc.container.container import Container
    if hasattr(app_context, '_container') and isinstance(app_context._container, Container):
        registry = app_context._container.registry

        print("4️⃣ 容器中的 SecurityEntityConfiguration 相关 Bean:")
        found_beans = []
        for name, definition in registry._services.items():
            if 'security_entity_configuration' in name.lower():
                found_beans.append((name, definition.service_type.__name__))
                print(f"   - {name}: {definition.service_type.__name__}")

        if len(found_beans) == 1:
            print(f"   预期: 只有 1 个 Bean")
            print(f"   结果: ✅ 正确（父类被替换）\n")
        else:
            print(f"   预期: 只有 1 个 Bean")
            print(f"   结果: ❌ 错误（找到 {len(found_beans)} 个）\n")

    # 最终验证
    all_passed = (
            type(config).__name__ == 'CustomSecurityEntityConfiguration' and
            config.user_orm_model == CustomUser and
            config.user_orm_model.__tablename__ == 'custom_users'
    )

    print("=" * 80)
    if all_passed:
        print("🎉 所有测试通过！继承替换机制正常工作！")
    else:
        print("❌ 部分测试失败")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    result = test_inheritance_replacement()
    sys.exit(0 if result else 1)
