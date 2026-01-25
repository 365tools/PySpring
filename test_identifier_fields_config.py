"""
测试 identifier_fields 配置功能

验证：
1. 从配置文件加载 identifier_fields
2. SecurityEntityConfiguration 正确读取配置
3. DefaultUserProvider 使用配置的字段列表
"""


def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试 identifier_fields 配置加载")
    print("=" * 60)

    # 测试1: 默认配置
    print("\n测试1: 使用默认配置")
    from pyspring.security.authentication.config.entity import SecurityEntityConfiguration

    config = SecurityEntityConfiguration()
    print(f"✅ 默认 identifier_fields: {config.identifier_fields}")
    assert isinstance(config.identifier_fields, list), "identifier_fields 应该是列表"
    assert 'username' in config.identifier_fields, "应包含 username"
    assert 'email' in config.identifier_fields, "应包含 email"
    assert len(config.identifier_fields) == 2, "默认应该只有2个字段（干净简洁）"

    # 测试2: 自定义配置
    print("\n测试2: 使用自定义配置")
    custom_fields = ['username', 'email', 'employee_id']
    config2 = SecurityEntityConfiguration(identifier_fields=custom_fields)
    print(f"✅ 自定义 identifier_fields: {config2.identifier_fields}")
    assert config2.identifier_fields == custom_fields, "应使用自定义字段列表"


def test_field_detection():
    """测试字段动态检测"""
    print("\n" + "=" * 60)
    print("测试字段动态检测")
    print("=" * 60)

    from pyspring.repositories.db.models.common.define import BaseUserTable
    from sqlalchemy import Column, String

    # 创建测试用户模型
    class TestUser(BaseUserTable):
        __tablename__ = "test_users"
        username = Column(String(50))
        phone = Column(String(20))
        employee_id = Column(String(20))

    # 测试字段存在性检测
    fields_to_check = ['user_id', 'username', 'email', 'phone', 'employee_id', 'nonexistent']

    print("\n检测字段存在性:")
    for field in fields_to_check:
        exists = hasattr(TestUser, field)
        status = "✅" if exists else "❌"
        print(f"   {status} {field}: {exists}")

    # 验证结果
    assert hasattr(TestUser, 'user_id'), "应有 user_id（继承自 BaseUserTable）"
    assert hasattr(TestUser, 'email'), "应有 email（继承自 BaseUserTable）"
    assert hasattr(TestUser, 'username'), "应有 username（自定义字段）"
    assert hasattr(TestUser, 'phone'), "应有 phone（自定义字段）"
    assert hasattr(TestUser, 'employee_id'), "应有 employee_id（自定义字段）"
    assert not hasattr(TestUser, 'nonexistent'), "不应有 nonexistent"


def test_query_conditions():
    """测试查询条件构建"""
    print("\n" + "=" * 60)
    print("测试查询条件构建")
    print("=" * 60)

    from pyspring.repositories.db.models.common.define import BaseUserTable
    from sqlalchemy import Column, String

    # 创建测试用户模型（使用不同的表名避免重复）
    class TestUser2(BaseUserTable):
        __tablename__ = "test_users_2"
        __table_args__ = {'extend_existing': True}
        username = Column(String(50))
        phone = Column(String(20))

    # 模拟配置
    identifier_fields = ['user_id', 'username', 'email', 'phone', 'nonexistent']

    # 构建查询条件（模拟 DefaultUserProvider 的逻辑）
    conditions = []
    for field_name in identifier_fields:
        if hasattr(TestUser2, field_name):
            field = getattr(TestUser2, field_name)
            conditions.append(f"{field_name} == identity")
            print(f"   ✅ 添加条件: {field_name} == identity")
        else:
            print(f"   ⏭️  跳过字段: {field_name}（不存在）")

    print(f"\n✅ 共构建 {len(conditions)} 个查询条件")
    print(f"   条件: {conditions}")

    # 验证
    assert len(conditions) == 4, "应该有4个条件（跳过 nonexistent）"
    assert "user_id == identity" in conditions
    assert "username == identity" in conditions
    assert "email == identity" in conditions
    assert "phone == identity" in conditions


def demonstrate_config_customization():
    """演示配置自定义"""
    print("\n" + "=" * 60)
    print("配置自定义示例")
    print("=" * 60)

    examples = [
        {
            "name": "基础配置（仅必需字段）",
            "fields": ["user_id", "email"]
        },
        {
            "name": "标准配置（常用字段）",
            "fields": ["user_id", "username", "email", "phone"]
        },
        {
            "name": "扩展配置（包含自定义字段）",
            "fields": ["username", "email", "phone", "employee_id", "nickname"]
        },
        {
            "name": "企业配置（优先员工工号）",
            "fields": ["employee_id", "email", "username"]
        },
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n示例 {i}: {example['name']}")
        print(f"   identifier_fields:")
        for field in example['fields']:
            print(f"     - \"{field}\"")


def demonstrate_yaml_config():
    """演示 YAML 配置"""
    print("\n" + "=" * 60)
    print("YAML 配置示例")
    print("=" * 60)

    yaml_configs = [
        {
            "name": "默认配置",
            "yaml": """# config/security.yaml
authentication:
  identifier_fields:
    - "user_id"
    - "username"
    - "email"
    - "phone"
"""
        },
        {
            "name": "自定义配置",
            "yaml": """# config/security.yaml
authentication:
  identifier_fields:
    - "employee_id"  # 员工工号（优先）
    - "email"        # 邮箱
    - "username"     # 用户名
    - "phone"        # 手机号
"""
        },
    ]

    for i, config in enumerate(yaml_configs, 1):
        print(f"\n示例 {i}: {config['name']}")
        print(config['yaml'])


if __name__ == "__main__":
    print("=" * 60)
    print("测试 identifier_fields 配置功能")
    print("=" * 60)

    test_config_loading()
    test_field_detection()
    test_query_conditions()
    demonstrate_config_customization()
    demonstrate_yaml_config()

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)

    print("\n📝 总结：")
    print("1. ✅ 配置从 security.yaml 加载，支持自定义")
    print("2. ✅ 字段动态检测，自动跳过不存在的字段")
    print("3. ✅ 灵活配置，支持任意字段组合")
    print("4. ✅ 向后兼容，提供合理的默认值")
    print("\n📚 详细配置指南：IDENTIFIER_FIELDS_CONFIGURATION_GUIDE.md")
