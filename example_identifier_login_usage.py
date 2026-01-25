"""
实际使用示例：identifier 登录

演示如何在 FastAPI 应用中使用 identifier 登录功能
"""
from typing import Optional


# 模拟数据库用户
class MockUser:
    def __init__(self, id: int, user_id: str, username: str, email: str, phone: Optional[str], password: str):
        self.id = id
        self.user_id = user_id
        self.username = username
        self.email = email
        self.phone = phone
        self.password = password
        self.active = True


# 模拟用户数据库
MOCK_USERS = [
    MockUser(
        id=1,
        user_id="550e8400-e29b-41d4-a716-446655440000",
        username="admin",
        email="admin@example.com",
        phone="13800138000",
        password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNd.OwVgKi"  # admin123
    ),
    MockUser(
        id=2,
        user_id="550e8400-e29b-41d4-a716-446655440001",
        username="user1",
        email="user1@example.com",
        phone="13900139000",
        password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNd.OwVgKi"
    ),
]


def find_user_by_identifier(identifier: str) -> Optional[MockUser]:
    """
    模拟 DefaultUserProvider.get_user_by_identity 的行为
    
    支持通过以下字段查找用户：
    - user_id
    - username
    - email
    - phone
    """
    for user in MOCK_USERS:
        if (user.user_id == identifier or
                user.username == identifier or
                user.email == identifier or
                (user.phone and user.phone == identifier)):
            return user
    return None


def demonstrate_identifier_login():
    """演示 identifier 登录的各种场景"""

    print("=" * 60)
    print("identifier 登录示例")
    print("=" * 60)

    test_cases = [
        {
            "description": "通过邮箱登录",
            "identifier": "admin@example.com",
            "expected_username": "admin"
        },
        {
            "description": "通过用户名登录",
            "identifier": "admin",
            "expected_username": "admin"
        },
        {
            "description": "通过手机号登录",
            "identifier": "13800138000",
            "expected_username": "admin"
        },
        {
            "description": "通过用户ID登录",
            "identifier": "550e8400-e29b-41d4-a716-446655440000",
            "expected_username": "admin"
        },
        {
            "description": "不存在的用户",
            "identifier": "nonexistent@example.com",
            "expected_username": None
        },
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test['description']}")
        print(f"   Identifier: {test['identifier']}")

        user = find_user_by_identifier(test['identifier'])

        if user:
            print(f"   ✅ 找到用户: {user.username}")
            print(f"   用户信息:")
            print(f"      - ID: {user.id}")
            print(f"      - User ID: {user.user_id}")
            print(f"      - Username: {user.username}")
            print(f"      - Email: {user.email}")
            print(f"      - Phone: {user.phone}")
            assert user.username == test['expected_username'], f"期望 {test['expected_username']}, 实际 {user.username}"
        else:
            print(f"   ❌ 未找到用户")
            assert test['expected_username'] is None, f"期望找到用户，但未找到"

    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)


def demonstrate_api_usage():
    """演示 API 调用示例"""

    print("\n" + "=" * 60)
    print("API 调用示例")
    print("=" * 60)

    examples = [
        {
            "method": "POST",
            "url": "/api/auth/login",
            "description": "使用邮箱登录",
            "body": {
                "identifier": "admin@example.com",
                "password": "admin123"
            }
        },
        {
            "method": "POST",
            "url": "/api/auth/login",
            "description": "使用用户名登录",
            "body": {
                "identifier": "admin",
                "password": "admin123"
            }
        },
        {
            "method": "POST",
            "url": "/api/auth/login",
            "description": "使用手机号登录",
            "body": {
                "identifier": "13800138000",
                "password": "admin123"
            }
        },
        {
            "method": "POST",
            "url": "/api/auth/login",
            "description": "使用 user_id（向后兼容）",
            "body": {
                "user_id": "admin",
                "password": "admin123"
            }
        },
        {
            "method": "POST",
            "url": "/api/auth/login",
            "description": "使用 email（向后兼容）",
            "body": {
                "email": "admin@example.com",
                "password": "admin123"
            }
        },
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n示例 {i}: {example['description']}")
        print(f"   {example['method']} {example['url']}")
        print(f"   请求体:")
        import json
        print(f"   {json.dumps(example['body'], indent=6, ensure_ascii=False)}")


def demonstrate_curl_commands():
    """演示 curl 命令示例"""

    print("\n" + "=" * 60)
    print("cURL 命令示例")
    print("=" * 60)

    curl_commands = [
        {
            "description": "使用邮箱登录",
            "command": """curl -X POST http://localhost:8000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "identifier": "admin@example.com",
    "password": "admin123"
  }'"""
        },
        {
            "description": "使用用户名登录",
            "command": """curl -X POST http://localhost:8000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "identifier": "admin",
    "password": "admin123"
  }'"""
        },
        {
            "description": "使用手机号登录",
            "command": """curl -X POST http://localhost:8000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "identifier": "13800138000",
    "password": "admin123"
  }'"""
        },
    ]

    for i, cmd in enumerate(curl_commands, 1):
        print(f"\n示例 {i}: {cmd['description']}")
        print(cmd['command'])


if __name__ == "__main__":
    demonstrate_identifier_login()
    demonstrate_api_usage()
    demonstrate_curl_commands()

    print("\n" + "=" * 60)
    print("✅ 所有演示完成！")
    print("=" * 60)

    print("\n📝 关键点:")
    print("1. identifier 可以是：用户名、邮箱、手机号、用户ID")
    print("2. 框架自动检测用户模型字段并支持查询")
    print("3. 保持向后兼容（user_id, email 字段仍然有效）")
    print("4. 安全特性不变（防时序攻击、密码验证）")

    print("\n📦 示例用户:")
    print("   - Username: admin")
    print("   - Email: admin@example.com")
    print("   - Phone: 13800138000")
    print("   - Password: admin123")
