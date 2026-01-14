"""
自定义认证提供者示例

本示例展示了如何扩展 PySpring 的认证系统，实现一个自定义的 API Key 认证提供者。
这种方式非常适合集成第三方认证服务、旧系统或特殊的认证协议。

使用方法:
1. 定义继承自 BaseAuthenticationProvider 的类
2. 注册提供者类型到 AuthProviderFactory
3. 初始化并测试认证
"""
import sys
from pathlib import Path
from typing import Optional

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from fastapi import Request
from pyspring.security.authentication.providers.base import BaseAuthenticationProvider, AuthenticationResult
from pyspring.security.authentication.core.factory import AuthProviderFactory
from pyspring.security.authentication.core.chain import AuthenticationChain


# =============================================================================
# 1. 定义自定义认证提供者
# =============================================================================

class ApiKeyAuthenticationProvider(BaseAuthenticationProvider):
    """
    自定义 API Key 认证提供者
    
    验证 HTTP 头中的 X-API-KEY
    """

    async def extract_credentials(self, request: Request) -> Optional[str]:
        """第一步：从请求头提取 API Key"""
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            print(f"[ApiKeyProvider] 提取到 API Key: {api_key}")
            return api_key
        return None

    async def validate_credentials(self, credentials: str) -> AuthenticationResult:
        """第二步：验证 API Key 有效性"""
        # 在实际应用中，这里应该查询数据库
        valid_keys = {"sk_live_123456": "admin", "sk_test_abcdef": "developer"}

        if credentials in valid_keys:
            role = valid_keys[credentials]
            print(f"[ApiKeyProvider] 验证成功，角色: {role}")
            return AuthenticationResult(
                success=True,
                user_id=credentials,
                username=f"user_{role}",
                roles=[role],
                provider_name=self.name
            )

        print(f"[ApiKeyProvider] 验证失败: {credentials}")
        return AuthenticationResult(
            success=False,
            error_message="Invalid API Key",
            provider_name=self.name
        )


# =============================================================================
# 2. 注册与测试脚本
# =============================================================================

async def main():
    print("=" * 60)
    print("🚀 自定义认证扩展示例")
    print("=" * 60)

    # 1. 注册新的提供者类型
    # 这样系统在读取配置时遇到 type: "api_key" 就能知道使用哪个类
    AuthProviderFactory.register_provider_type("api_key", ApiKeyAuthenticationProvider)

    # 2. 模拟配置 (通常来自 security.yaml)
    # 在真实项目中，你只需在 YAML 中配置，无需手动创建
    mock_config = {
        "type": "api_key",  # 对应上面注册的 key
        "enabled": True,
        "priority": 10  # 高优先级
    }

    # 3. 创建提供者实例
    print("\n📦 创建提供者实例...")
    provider = AuthProviderFactory.create_provider(
        provider_config={**mock_config, "name": "custom_api_key_provider"}
    )

    # 4. 构建认证链
    print("🔗 构建认证链...")
    chain = AuthenticationChain()
    chain.register_provider(provider)

    # 5. 模拟请求测试
    from unittest.mock import MagicMock

    # 测试用例 1: 有效 Key
    print("\n🧪 测试 1: 发送有效 API Key")
    mock_request_valid = MagicMock(spec=Request)
    mock_request_valid.headers = {"X-API-KEY": "sk_live_123456"}
    mock_request_valid.url.path = "/api/v1/resource"

    result = await chain.authenticate(mock_request_valid)
    assert result.success is True
    print(f"✅ 认证结果: 通过 (User: {result.username})")

    # 测试用例 2: 无效 Key
    print("\n🧪 测试 2: 发送无效 API Key")
    mock_request_invalid = MagicMock(spec=Request)
    mock_request_invalid.headers = {"X-API-KEY": "wrong_key"}
    mock_request_invalid.url.path = "/api/v1/resource"

    result = await chain.authenticate(mock_request_invalid)
    assert result.success is False
    print(f"❌ 认证结果: 拒绝 ({result.error_message})")

    # 测试用例 3: 无 Key (跳过)
    print("\n🧪 测试 3: 不发送 API Key")
    mock_request_none = MagicMock(spec=Request)
    mock_request_none.headers = {}
    mock_request_none.url.path = "/api/v1/resource"

    # AuthChain 如果所有 provider 都无法认证，且非公开路径，则返回失败
    result = await chain.authenticate(mock_request_none)
    print(f"⏭️ 认证结果: {result.success} (Reason: {result.error_message})")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
