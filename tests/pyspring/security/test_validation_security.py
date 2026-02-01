"""
测试 ValidationError 敏感信息过滤
"""
from pydantic import BaseModel, ValidationError, Field


class SensitiveModel(BaseModel):
    username: str
    password: str
    email: str
    is_active: bool = Field(alias="active")

    class Config:
        populate_by_name = True


# 模拟数据库对象
class User:
    def __init__(self):
        self.id = 1
        self.username = "admin"
        self.email = "admin@example.com"
        self.password = "$2b$12$secrethash"
        self.active = True  # 注意：是 active 不是 is_active


def test_validation():
    """测试验证错误"""
    print("=" * 60)
    print("🧪 测试 ValidationError 处理")
    print("=" * 60)

    user = User()

    try:
        # 这会触发 ValidationError，因为没有 is_active 字段
        result = SensitiveModel.model_validate(user)
        print(f"✅ 验证成功: {result}")
    except ValidationError as e:
        print(f"\n❌ ValidationError:")
        for error in e.errors():
            error_input = error.get("input")

            # 模拟框架的过滤逻辑
            safe_input = None
            if isinstance(error_input, dict):
                safe_input = f"<object with {len(error_input)} fields>"
            elif hasattr(error_input, "__class__"):
                safe_input = f"<{error_input.__class__.__name__} object>"
            elif isinstance(error_input, (str, int, float, bool, type(None))):
                safe_input = error_input
            else:
                safe_input = "<complex object>"

            print(f"\n  字段: {error['loc']}")
            print(f"  消息: {error['msg']}")
            print(f"  类型: {error['type']}")
            print(f"  原始 input: {error_input}")
            print(f"  ✅ 安全 input: {safe_input}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_validation()
