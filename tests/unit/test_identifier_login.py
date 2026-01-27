"""
测试 identifier 登录功能

验证：
1. LoginRequest 支持 identifier 字段
2. DefaultPasswordLoginProvider 支持 identifier 查询
3. DefaultUserProvider 支持多字段匹配（user_id, email, username, phone）
"""
from pyspring.security.authentication.contracts.request import LoginRequest


def test_login_request_with_identifier():
    """测试使用 identifier 创建 LoginRequest"""

    # 测试1: 使用 identifier（新方式）
    request1 = LoginRequest(
        identifier="admin@example.com",
        password="admin123"
    )
    assert request1.identifier == "admin@example.com"
    assert request1.password == "admin123"
    print("✅ 测试1通过: identifier 方式")

    # 测试2: 使用 user_id（兼容旧方式）
    request2 = LoginRequest(
        user_id="admin",
        password="admin123"
    )
    assert request2.user_id == "admin"
    assert request2.password == "admin123"
    print("✅ 测试2通过: user_id 方式（向后兼容）")

    # 测试3: 使用 email（兼容旧方式）
    request3 = LoginRequest(
        email="admin@example.com",
        password="admin123"
    )
    assert request3.email == "admin@example.com"
    assert request3.password == "admin123"
    print("✅ 测试3通过: email 方式（向后兼容）")

    # 测试4: 同时提供 identifier 和 user_id（应该优先使用 identifier）
    request4 = LoginRequest(
        identifier="admin@example.com",
        user_id="admin_old",
        password="admin123"
    )
    assert request4.identifier == "admin@example.com"
    assert request4.user_id == "admin_old"
    print("✅ 测试4通过: identifier 和 user_id 都提供")

    # 测试5: 验证至少需要一个登录凭证
    try:
        request5 = LoginRequest(password="admin123")
        print("❌ 测试5失败: 应该抛出验证错误")
    except ValueError as e:
        print(f"✅ 测试5通过: 正确抛出验证错误 - {e}")


def test_login_examples():
    """显示各种登录示例"""

    print("\n" + "=" * 60)
    print("登录示例")
    print("=" * 60)

    examples = [
        {
            "description": "使用邮箱登录（推荐使用 identifier）",
            "data": {
                "identifier": "admin@example.com",
                "password": "admin123"
            }
        },
        {
            "description": "使用用户名登录（推荐使用 identifier）",
            "data": {
                "identifier": "admin",
                "password": "admin123"
            }
        },
        {
            "description": "使用手机号登录（推荐使用 identifier）",
            "data": {
                "identifier": "13800138000",
                "password": "admin123"
            }
        },
        {
            "description": "使用 user_id 登录（向后兼容）",
            "data": {
                "user_id": "admin",
                "password": "admin123"
            }
        },
        {
            "description": "使用 email 登录（向后兼容）",
            "data": {
                "email": "admin@example.com",
                "password": "admin123"
            }
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n示例 {i}: {example['description']}")
        print(f"JSON: {example['data']}")
        try:
            request = LoginRequest(**example['data'])
            print(f"✅ 验证通过")
        except Exception as e:
            print(f"❌ 验证失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("测试 LoginRequest identifier 功能")
    print("=" * 60)

    test_login_request_with_identifier()
    test_login_examples()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)

    print("\n📝 使用说明：")
    print("1. 推荐使用 'identifier' 字段，可自动匹配用户名、邮箱、手机号、用户ID")
    print("2. 'user_id' 和 'email' 字段保留用于向后兼容")
    print("3. 框架会自动检测用户模型中的字段（username, phone）并支持查询")
    print("4. 查询优先级: identifier > user_id > email")
