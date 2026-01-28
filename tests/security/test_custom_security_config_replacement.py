"""
测试自定义 SecurityEntityConfiguration 替换机制

测试场景：
1. 框架默认使用 UserTable（表名：pyspring_user）
2. 用户通过 @Component 自定义 CustomSecurityEntityConfiguration
3. 验证 IoC 容器是否使用自定义的 User 模型（表名：custom_users）
4. 验证数据库查询是否使用正确的表

预期结果：
- IoC 容器使用 CustomSecurityEntityConfiguration
- user_orm_model 是自定义的 CustomUser
- 生成的 SQL 查询 custom_users 表，而不是 pyspring_user
"""
import sys
from pathlib import Path

# 设置控制台UTF-8编码
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# 确保可以导入 pyspring
sys.path.insert(0, str(Path(__file__).parent / "src"))

from sqlalchemy import Column, String, select, or_

from pyspring.ioc import ApplicationContext
from pyspring.ioc.annotations import Component
from pyspring.repositories.db.models.common.define import BaseUserTable
from pyspring.security.authentication.config.entity import SecurityEntityConfiguration
from pyspring.security.orm.tables import UserTable


# ============================================================
# 1. 定义自定义 User 模型（模拟 example 中的 app/models/user.py）
# ============================================================
class CustomUser(BaseUserTable):
    """
    自定义用户模型
    
    模拟 example 项目中的 User 模型
    继承自 BaseUserTable，自定义表名
    """
    __tablename__ = "custom_users"

    # 自定义字段（和 example 一样）
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    phone = Column(String(20), nullable=True, comment="手机号")

    def __repr__(self):
        return f"<CustomUser(username={self.username}, email={self.email})>"


# ============================================================
# 2. 定义自定义配置（模拟 example 中的 app/config/security_config.py）
# ============================================================
@Component
class CustomSecurityEntityConfiguration(SecurityEntityConfiguration):
    """
    自定义安全实体配置
    
    模拟 example 项目中的配置方式：
    - 使用 @Component 装饰器
    - 继承 SecurityEntityConfiguration
    - 重写 user_orm_model
    """

    def __init__(self):
        super().__init__()  # 继承所有默认值

        # 重写用户模型
        self.user_orm_model = CustomUser  # ✅ 使用自定义的 CustomUser 模型

        print(f"✅ CustomSecurityEntityConfiguration 初始化")
        print(f"   user_orm_model = {self.user_orm_model}")
        print(f"   表名 = {self.user_orm_model.__tablename__}")


# ============================================================
# 3. 测试函数
# ============================================================
def test_security_config_replacement():
    """测试自定义配置是否替换了框架默认配置"""
    print("\n" + "=" * 80)
    print("测试：CustomSecurityEntityConfiguration 替换机制")
    print("=" * 80 + "\n")

    # 步骤 1：初始化 ApplicationContext（先扫描框架，再扫描用户包）
    print("📦 步骤 1/5: 初始化 IoC 容器...")
    print("   扫描包: [__main__]")
    print("   预期:")
    print("   - 框架自动扫描 pyspring.security.authentication.config.entity.SecurityEntityConfiguration")
    print("   - 用户扫描 __main__.CustomSecurityEntityConfiguration")
    print("   - 因父类有 @ConditionalOnMissingBean，子类应替换父类\n")

    app_context = ApplicationContext.initialize(
        base_packages=[__name__],  # 只扫描用户包
        enable_aop=False
    )
    print(f"✅ IoC 容器初始化完成\n")

    # 调试：打印所有注册的 Bean
    print("🔍 调试：容器中注册的所有SecurityEntityConfiguration相关Bean...")
    from pyspring.ioc.container.container import Container
    if hasattr(app_context, '_container') and isinstance(app_context._container, Container):
        registry = app_context._container.registry
        for name, definition in registry._services.items():
            if 'SecurityEntityConfiguration' in name or 'SecurityEntityConfiguration' in str(definition.service_type):
                print(f"   - Bean名称: {name}")
                print(f"     类型: {definition.service_type}")
                print(f"     is_conditional: {definition.is_conditional}")
                print(f"     is_component: {not definition.is_bean}")
                print()

    # 步骤 2：获取 SecurityEntityConfiguration Bean
    print("🔍 步骤 2/5: 获取 SecurityEntityConfiguration Bean...")
    entity_config = app_context.get_bean(SecurityEntityConfiguration)
    print(f"✅ 获取到的 Bean 类型: {type(entity_config).__name__}")
    print(f"✅ Bean 类: {entity_config.__class__}")
    print(f"✅ 是否为自定义配置: {isinstance(entity_config, CustomSecurityEntityConfiguration)}\n")

    # 步骤 3：验证 user_orm_model
    print("👤 步骤 3/5: 验证 user_orm_model...")
    print(f"✅ user_orm_model 类型: {entity_config.user_orm_model}")
    print(f"✅ 表名: {entity_config.user_orm_model.__tablename__}")
    print(f"✅ 是否为 CustomUser: {entity_config.user_orm_model == CustomUser}")
    print(f"✅ 不是框架默认的 UserTable: {entity_config.user_orm_model != UserTable}\n")

    # 步骤 4：验证 identifier_fields 配置
    print("⚙️  步骤 4/5: 验证 identifier_fields 配置...")
    print(f"✅ identifier_fields: {entity_config.identifier_fields}")
    print(f"✅ 字段数量: {len(entity_config.identifier_fields)}\n")

    # 步骤 5：生成 SQL 查询（模拟 DefaultUserProvider.get_user_by_identity）
    print("🗄️  步骤 5/5: 生成 SQL 查询语句...")
    user_model = entity_config.user_orm_model
    identifier = "test@example.com"
    identifier_fields = entity_config.identifier_fields

    # 构建查询条件（和 DefaultUserProvider 一样的逻辑）
    conditions = []
    for field_name in identifier_fields:
        if hasattr(user_model, field_name):
            field = getattr(user_model, field_name)
            conditions.append(field == identifier)
            print(f"   • 字段 '{field_name}' 存在，已添加到查询条件")

    stmt = select(user_model).where(or_(*conditions))
    sql_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))

    print(f"\n生成的 SQL:")
    print(f"   {sql_str}\n")

    # 验证结果
    print("=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80 + "\n")

    checks = {
        "✅ IoC 容器使用 CustomSecurityEntityConfiguration": isinstance(entity_config, CustomSecurityEntityConfiguration),
        "✅ user_orm_model 是 CustomUser": entity_config.user_orm_model == CustomUser,
        "✅ 不是框架默认的 UserTable": entity_config.user_orm_model != UserTable,
        "✅ 表名是 custom_users": entity_config.user_orm_model.__tablename__ == "custom_users",
        "✅ SQL 查询 custom_users 表": "custom_users" in sql_str.lower(),
        "✅ SQL 不查询 pyspring_user 表": "pyspring_user" not in sql_str.lower(),
    }

    all_passed = True
    for check, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check}")
        if not result:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有测试通过！自定义配置替换成功！")
    else:
        print("❌ 部分测试失败！")
    print("=" * 80 + "\n")

    return all_passed


def test_compare_with_default():
    """对比测试：展示没有自定义配置时的默认行为"""
    print("\n" + "=" * 80)
    print("对比测试：框架默认配置（无自定义）")
    print("=" * 80 + "\n")

    print("📦 创建默认配置实例...")
    from pyspring.security.authentication.config.entity import SecurityEntityConfiguration as DefaultConfig
    default_config = DefaultConfig()

    print(f"✅ 默认配置类型: {type(default_config).__name__}")
    print(f"✅ 默认 user_orm_model: {default_config.user_orm_model}")
    print(f"✅ 默认表名: {default_config.user_orm_model.__tablename__}\n")

    # 生成默认 SQL
    user_model = default_config.user_orm_model
    identifier_fields = default_config.identifier_fields
    identifier = "test@example.com"

    conditions = []
    for field_name in identifier_fields:
        if hasattr(user_model, field_name):
            field = getattr(user_model, field_name)
            conditions.append(field == identifier)

    stmt = select(user_model).where(or_(*conditions))
    sql_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))

    print(f"默认配置生成的 SQL:")
    print(f"   {sql_str}\n")

    print("=" * 80)
    print("📊 对比总结")
    print("=" * 80)
    print(f"框架默认: 查询 {default_config.user_orm_model.__tablename__} 表")
    print(f"自定义后: 查询 custom_users 表")
    print("=" * 80 + "\n")


def test_check_example_template():
    """检查 example 模板配置是否正确"""
    print("\n" + "=" * 80)
    print("检查：Example 模板配置")
    print("=" * 80 + "\n")

    template_dir = Path(__file__).parent / "src" / "pyspring" / "templates" / "example"

    checks = {
        "security_config.py.template": template_dir / "app" / "config" / "security_config.py.template",
        "user.py.template": template_dir / "app" / "models" / "user.py.template",
    }

    for name, file_path in checks.items():
        if file_path.exists():
            print(f"✅ 模板文件存在: {name}")

            content = file_path.read_text(encoding='utf-8')

            if name == "security_config.py.template":
                has_component = "@Component" in content
                has_inheritance = "SecurityEntityConfiguration" in content
                has_user_model = "self.user_orm_model = User" in content

                print(f"   • 包含 @Component: {has_component}")
                print(f"   • 继承 SecurityEntityConfiguration: {has_inheritance}")
                print(f"   • 配置 user_orm_model: {has_user_model}")

                if has_component and has_inheritance and has_user_model:
                    print(f"   ✅ {name} 配置正确\n")
                else:
                    print(f"   ❌ {name} 配置有问题\n")

            elif name == "user.py.template":
                has_basetable = "BaseUserTable" in content
                has_tablename = "__tablename__" in content
                has_username = "username" in content

                print(f"   • 继承 BaseUserTable: {has_basetable}")
                print(f"   • 定义 __tablename__: {has_tablename}")
                print(f"   • 定义 username 字段: {has_username}")

                if has_basetable and has_tablename and has_username:
                    print(f"   ✅ {name} 配置正确\n")
                else:
                    print(f"   ❌ {name} 配置有问题\n")
        else:
            print(f"❌ 模板文件缺失: {name}")
            print(f"   路径: {file_path}\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PySpring CustomSecurityEntityConfiguration 替换机制测试")
    print("=" * 80)

    # 测试 1: 检查模板配置
    test_check_example_template()

    # 测试 2: 对比默认配置
    test_compare_with_default()

    # 测试 3: 测试自定义配置替换
    result = test_security_config_replacement()

    # 退出码
    sys.exit(0 if result else 1)
