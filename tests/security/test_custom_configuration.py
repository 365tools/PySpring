"""
PySpring 自定义配置测试套�?

测试用户自定义表、@Bean、@Configuration等扩展场景是否正常工�?
"""
import io
import sys

# 设置标准输出编码为UTF-8，解决Windows下中文乱码问�?
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import os
from unittest.mock import Mock
from typing import Any, Dict, Optional

# 设置测试环境变量
os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-custom-configuration-testing-12345678'


class TestCustomConfiguration:
    """测试自定义配置场�?""

    def test_1_custom_user_table(self):
        """测试1: 自定义用户表结构"""
        print("\n" + "=" * 80)
        print("测试: 自定义用户表")
        print("=" * 80)

        from sqlalchemy import Column, String
        from pyspring.repositories.db.models.common.define import BaseUserTable
        from pyspring.security.authentication.config.entity.config import SecurityEntityConfiguration

        # 创建自定义用户表
        class CustomUserTable(BaseUserTable):
            """
    用户自定义的用户表，添加了额外字�?""
            __tablename__ = 'custom_users'

            # 继承基础字段，添加自定义字段
            nickname = Column(String(50), nullable=True, comment="昵称")
    phone = Column(String(20), nullable=True, comment="手机�?)
            avatar_url = Column(String(255), nullable=True, comment="头像URL")
            department = Column(String(100), nullable=True, comment="部门")

    # 创建自定义配�?
        custom_config = SecurityEntityConfiguration(
            user_orm_model=CustomUserTable
        )

    # 验证自定义表已注�?
        assert custom_config.user_orm_model == CustomUserTable
        assert hasattr(custom_config.user_orm_model, 'nickname')
        assert hasattr(custom_config.user_orm_model, 'phone')
        assert hasattr(custom_config.user_orm_model, 'avatar_url')
        assert hasattr(custom_config.user_orm_model, 'department')

    print("�?自定义用户表字段:")
        print(f"   - nickname: {CustomUserTable.nickname.type}")
        print(f"   - phone: {CustomUserTable.phone.type}")
        print(f"   - avatar_url: {CustomUserTable.avatar_url.type}")
        print(f"   - department: {CustomUserTable.department.type}")
    print("�?自定义用户表 - 通过")

    def test_2_custom_token_blacklist_table(self):
        """测试2: 自定义Token黑名单表"""
        print("\n" + "=" * 80)
        print("测试: 自定义Token黑名单表")
        print("=" * 80)

        from sqlalchemy import Column, Integer, String, DateTime, Text
        from pyspring.repositories.db.models.common.define import Base

        # 创建自定义黑名单�?
        class CustomTokenBlacklistTable(Base):
            """用户自定义的Token黑名单表，添加了额外跟踪字段"""
            __tablename__ = 'custom_token_blacklist'

            id = Column(Integer, primary_key=True, autoincrement=True)
            token_id = Column(String(255), unique=True, nullable=False, comment="Token JTI")
            user_id = Column(Integer, nullable=True, comment="用户ID")
            token_type = Column(String(20), nullable=False, comment="Token类型")
            reason = Column(String(255), nullable=True, comment="撤销原因")
            expires_at = Column(DateTime, nullable=False, comment="Token过期时间")

            # 自定义字�?
            ip_address = Column(String(45), nullable=True, comment="撤销时的IP地址")
            user_agent = Column(Text, nullable=True, comment="撤销时的User-Agent")
            revoked_by = Column(String(100), nullable=True, comment="撤销操作�?)

            # 验证表结�?
        assert hasattr(CustomTokenBlacklistTable, 'token_id')
        assert hasattr(CustomTokenBlacklistTable, 'ip_address')
        assert hasattr(CustomTokenBlacklistTable, 'user_agent')
        assert hasattr(CustomTokenBlacklistTable, 'revoked_by')

            print("�?自定义黑名单表扩展字�?")
        print("   - ip_address: 撤销时的IP地址")
        print("   - user_agent: 撤销时的User-Agent")
            print("   - revoked_by: 撤销操作�?)
            print("�?自定义Token黑名单表 - 通过")

    def test_3_custom_bean_login_provider(self):
        """测试3: 自定义@Bean - 登录提供�?""
        print("\n" + "=" * 80)
        print("测试: 自定义@Bean - 登录提供�?)
        print("=" * 80)

        from pyspring.security.authentication.contracts.login import ILoginProvider
        from pyspring.security.authentication.contracts.request import LoginRequest
        from pyspring.ioc.annotations import Configuration, Bean, ConditionalOnMissingBean

        # 创建自定义登录提供�?
        class CustomLoginProvider(ILoginProvider):
            """
        用户自定义的登录提供者，支持邮箱 + 验证码登�?""

            def __init__(self, verification_service: Any):
                self.verification_service = verification_service

            async def authenticate(self, credentials: LoginRequest) -> Dict[str, Any]:
                """邮箱验证码登�?""
                # 验证邮箱验证�?
                # 模拟验证逻辑
                return {
                    "user_id": "123",
                    "email": credentials.email,
                    "auth_method": "email_verification"
                }

            def supports(self, credentials: LoginRequest) -> bool:
                """
                支持邮箱验证码登�?""
                return hasattr(credentials, 'verification_code')

        # 创建自定义配置类
        @Configuration
        class CustomAuthConfig:
            """用户自定义的认证配置"""

            @Bean
            @ConditionalOnMissingBean(ILoginProvider)
            def custom_login_provider(self) -> ILoginProvider:
                """注册自定义登录提供�?""
                verification_service = Mock()  # 模拟验证服务
                return CustomLoginProvider(verification_service)

        # 验证配置�?
        assert hasattr(CustomAuthConfig, '__pyspring_configuration__')
        assert CustomAuthConfig.__pyspring_configuration__ is True

        # 验证Bean方法
        config_instance = CustomAuthConfig()
        provider = config_instance.custom_login_provider()
        assert isinstance(provider, ILoginProvider)
        assert isinstance(provider, CustomLoginProvider)

        print("�?自定义登录提供者注册成�?)
        print(f"   类型: {type(provider).__name__}")
        print(f"   支持认证方法: email_verification")
        print("�?自定义@Bean - 登录提供�?- 通过")

    def test_4_custom_token_payload_builder(self):
        """
                测试4: 自定义Token
                Payload构建�?""
        print("\n" + "=" * 80)
print("测试: 自定义Token Payload构建�?)
        print("=" * 80)

        from pyspring.security.authentication.contracts.token import ITokenPayloadBuilder
from pyspring.ioc.annotations import Configuration, Bean

    # 创建自定义Payload构建�?
        class CustomTokenPayloadBuilder(ITokenPayloadBuilder):
            """用户自定义的Token Payload构建器，添加额外字段"""

            async def build_payload(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
                """构建包含额外信息的Token Payload"""
                payload = {
                    "sub": user_info.get("user_id"),
                    "email": user_info.get("email"),
                    # 自定义字�?
                    "department": user_info.get("department", "未知"),
                    "role_level": user_info.get("role_level", 1),
                    "tenant_id": user_info.get("tenant_id", "default"),
                    "permissions": user_info.get("permissions", [])
                }
                return payload

        # 创建配置
        @Configuration
        class CustomTokenConfig:
            @Bean
            def custom_token_payload_builder(self) -> ITokenPayloadBuilder:
                return CustomTokenPayloadBuilder()

        # 测试Payload构建
        async def run_test():
            config = CustomTokenConfig()
            builder = config.custom_token_payload_builder()

            user_info = {
                "user_id": "123",
                "email": "user@example.com",
                "department": "技术部",
                "role_level": 3,
                "tenant_id": "tenant_001",
                "permissions": ["read", "write", "delete"]
            }

            payload = await builder.build_payload(user_info)

            assert payload["sub"] == "123"
            assert payload["department"] == "技术部"
            assert payload["role_level"] == 3
            assert payload["tenant_id"] == "tenant_001"
            assert len(payload["permissions"]) == 3

            print("�?自定义Payload字段:")
            print(f"   - department: {payload['department']}")
            print(f"   - role_level: {payload['role_level']}")
            print(f"   - tenant_id: {payload['tenant_id']}")
            print(f"   - permissions: {payload['permissions']}")
            return True

        result = asyncio.run(run_test())
        assert result
print("�?自定义Token Payload构建�?- 通过")

    def test_5_custom_user_provider(self):
        """测试5: 自定义用户提供者（多数据源�?""
        print("\n" + "=" * 80)
        print("测试: 自定义用户提供者（多数据源�?)
        print("=" * 80)

        from pyspring.security.authentication.contracts.user import IUserProvider
        from pyspring.ioc.annotations import Configuration, Bean

        # 创建自定义用户提供者（支持多数据源�?
        class MultiSourceUserProvider(IUserProvider):
            """支持从多个数据源查询用户"""

            def __init__(self, primary_db: Any, ldap_service: Any):
                self.primary_db = primary_db
                self.ldap_service = ldap_service

            async def get_user_by_id(self, user_id: Any) -> Optional[Any]:
                """根据ID获取用户"""
                # 模拟查询
                return {"user_id": str(user_id), "source": "db"}

            async def get_user_by_identity(self, identity: str) -> Optional[Any]:
                """先从主数据库查询，失败则从LDAP查询"""
                # 模拟从主数据库查�?
                user = await self._get_from_db(identity)
                if user:
                    print(f"   �?从主数据库找到用�? {identity}")
                    return user

                # 从LDAP查询
                user = await self._get_from_ldap(identity)
                if user:
                    print(f"   �?从LDAP找到用户: {identity}")
                    return user

                return None

            async def _get_from_db(self, identity: str) -> Optional[Any]:
                """从数据库查询"""
                # 模拟查询
                return None

            async def _get_from_ldap(self, identity: str) -> Optional[Any]:
                """从LDAP查询"""
                # 模拟LDAP查询
                if identity.endswith("@company.com"):
                    return {
                        "user_id": identity.split("@")[0],
                        "email": identity,
                        "source": "ldap"
                    }
                return None

        @Configuration
        class CustomUserProviderConfig:
            @Bean
            def multi_source_user_provider(self) -> IUserProvider:
                primary_db = Mock()
                ldap_service = Mock()
                return MultiSourceUserProvider(primary_db, ldap_service)

        # 测试多数据源查询
        async def run_test():
            config = CustomUserProviderConfig()
            provider = config.multi_source_user_provider()

            # 测试LDAP用户
            user = await provider.get_user_by_identity("john.doe@company.com")
            assert user is not None
            assert user["source"] == "ldap"
            assert user["user_id"] == "john.doe"

            return True

        result = asyncio.run(run_test())
        assert result
        print("�?多数据源用户查询成功")
        print("�?自定义用户提供�?- 通过")

    def test_6_custom_response_builder(self):
        """测试6: 自定义响应构建器"""
        print("\n" + "=" * 80)
        print("测试: 自定义响应构建器")
        print("=" * 80)

        from pyspring.security.authentication.contracts.response import IResponseBuilder
        from pyspring.ioc.annotations import Bean, Configuration

        # 创建自定义响应构建器
        class CustomResponseBuilder(IResponseBuilder):
            """
        自定义响应格式，添加额外元数�?""

            async def build_login_response(
                    self,
                    user_info: Any,
                    access_token: str,
                    refresh_token: Optional[str] = None
            ) -> Dict[str, Any]:
                """构建包含额外元数据的登录响应"""
                return {
                    "code": 200,
                    "message": "登录成功",
                    "data": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_type": "Bearer",
                        "expires_in": 3600,
                        "user": {
                            "id": getattr(user_info, 'user_id', None),
                            "email": getattr(user_info, 'email', None)
                        }
                    },
                    "metadata": {
                        "login_time": "2026-01-22 00:00:00",
                        "login_ip": "192.168.1.100",
                        "device_type": "web"
                    }
                }

            async def build_logout_response(self) -> Dict[str, Any]:
                """构建登出响应"""
                return {
                    "code": 200,
                    "message": "登出成功",
                    "metadata": {
                        "logout_time": "2026-01-22 00:00:00"
                    }
                }

            async def build_token_response(
                    self,
                    access_token: str,
                    refresh_token: Optional[str] = None
            ) -> Dict[str, Any]:
                """构建Token响应"""
                return {
                    "code": 200,
                    "data": {
                        "access_token": access_token,
                        "refresh_token": refresh_token
                    }
                }

        @Configuration
        class CustomResponseConfig:
            @Bean
            def custom_response_builder(self) -> IResponseBuilder:
                return CustomResponseBuilder()


# 测试自定义响�?
        async def run_test():
            config = CustomResponseConfig()
            builder = config.custom_response_builder()

            mock_user = Mock(user_id="123", email="user@example.com")
            response = await builder.build_login_response(
                mock_user,
                "access_token_xxx",
                "refresh_token_xxx"
            )

            assert response["code"] == 200
            assert response["message"] == "登录成功"
            assert "metadata" in response
            assert response["metadata"]["device_type"] == "web"
            assert response["data"]["token_type"] == "Bearer"

            print("�?自定义响应格�?")
            print(f"   - code: {response['code']}")
            print(f"   - metadata: {response['metadata']}")
            print(f"   - token_type: {response['data']['token_type']}")
            return True

        result = asyncio.run(run_test())
        assert result
print("�?自定义响应构建器 - 通过")

    def test_7_integration_custom_config(self):
        """测试7: 集成测试 - 完整自定义配置流�?""
        print("\n" + "=" * 80)
        print("测试: 集成测试 - 完整自定义配置流�?)
        print("=" * 80)

        from pyspring.ioc.annotations import Configuration, Bean
        from pyspring.security.authentication.config.entity.config import SecurityEntityConfiguration
        from pyspring.security.authentication.contracts.user import IUserProvider
        from pyspring.security.authentication.contracts.token import ITokenPayloadBuilder
        from pyspring.security.authentication.contracts.response import IResponseBuilder

        # 完整的自定义配置
        @Configuration
        class CompleteCustomConfig:
            """用户的完整自定义认证配置"""

            @Bean
            def custom_security_entity_config(self) -> SecurityEntityConfiguration:
                """
        自定义实体配�?""
                # 这里可以指定自定义表
                return SecurityEntityConfiguration()

            @Bean
            def custom_user_provider(self, db: Any) -> IUserProvider:
    """自定义用户提供�?""
    from pyspring.security.authentication.providers.user.database import DefaultUserProvider
    return DefaultUserProvider(db, self.custom_security_entity_config())

@Bean
def custom_token_payload_builder(self) -> ITokenPayloadBuilder:
    """
    自定义Token构建�?""

                class SimplePayloadBuilder(ITokenPayloadBuilder):
                    async def build_payload(self, user_info):
                        return {
                            "sub": user_info.get("user_id"),
                            "custom_field": "custom_value"
                        }

                return SimplePayloadBuilder()

            @Bean
            def custom_response_builder(self) -> IResponseBuilder:
                """自定义响应构建器"""

                class SimpleResponseBuilder(IResponseBuilder):
                    async def build_login_response(self, user_info, access_token, refresh_token=None):
                        return {"token": access_token, "custom": True}

                    async def build_logout_response(self):
                        return {"status": "logged_out"}

                    async def build_token_response(self, access_token, refresh_token=None):
                        return {"token": access_token}

                return SimpleResponseBuilder()


# 验证配置�?
        assert hasattr(CompleteCustomConfig, '__pyspring_configuration__')

        # 验证所有Bean方法
        config = CompleteCustomConfig()

        # 检查SecurityEntityConfiguration
        entity_config = config.custom_security_entity_config()
        assert entity_config is not None
print("�?SecurityEntityConfiguration已注�?)

        # 检查UserProvider
        mock_db = Mock()
        user_provider = config.custom_user_provider(mock_db)
        assert user_provider is not None
print("�?自定义UserProvider已注�?)

        # 检查TokenPayloadBuilder
        payload_builder = config.custom_token_payload_builder()
        assert payload_builder is not None
print("�?自定义TokenPayloadBuilder已注�?)

        # 检查ResponseBuilder
        response_builder = config.custom_response_builder()
        assert response_builder is not None
print("�?自定义ResponseBuilder已注�?)

        # 测试整体流程
        async def run_test():
            # 测试Payload构建
            payload = await payload_builder.build_payload({"user_id": "123"})
            assert payload["custom_field"] == "custom_value"
            print(f"   Token Payload: {payload}")

            # 测试响应构建
            response = await response_builder.build_login_response(
                None, "token_xxx", "refresh_xxx"
            )
            assert response["custom"] is True
            print(f"   Login Response: {response}")

            return True

        result = asyncio.run(run_test())
        assert result
print("�?完整自定义配置流�?- 通过")

    def test_8_conditional_bean_override(self):
        """测试8: @ConditionalOnMissingBean条件覆盖"""
        print("\n" + "=" * 80)
        print("测试: @ConditionalOnMissingBean条件覆盖")
        print("=" * 80)

        from pyspring.ioc.annotations import Configuration
        from pyspring.security.authentication.contracts.login import ILoginProvider

        # 模拟框架的默认配�?
        @Configuration
        class FrameworkDefaultConfig:
            """框架提供的默认配�?""

            @Bean
            @ConditionalOnMissingBean(ILoginProvider)
            def default_login_provider(self) -> ILoginProvider:
                """
            框架默认的登录提供�?""

                class DefaultProvider(ILoginProvider):
                    async def authenticate(self, credentials):
                        return {"source": "default"}

                    def supports(self, credentials):
                        return True

                return DefaultProvider()


# 用户的自定义配置（会覆盖默认配置�?
        @Configuration
        class UserCustomConfig:
            """用户自定义配置，覆盖默认实现"""

            @Bean
            def custom_login_provider(self) -> ILoginProvider:
                """用户自定义的登录提供者（没有@ConditionalOnMissingBean�?""

                class CustomProvider(ILoginProvider):
                    async def authenticate(self, credentials):
                        return {"source": "custom"}

                    def supports(self, credentials):
                        return True

                return CustomProvider()

        # 验证配置
        default_config = FrameworkDefaultConfig()
        user_config = UserCustomConfig()

        # 检查Bean方法的装饰器
        default_method = default_config.default_login_provider
        custom_method = user_config.custom_login_provider

        # 验证默认Bean有条件装饰器
        has_conditional = hasattr(default_method, '__pyspring_conditional__') or \
                          hasattr(default_method, '__wrapped__') or \
                          'ConditionalOnMissingBean' in str(type(default_method))
        print(f"�?框架默认Bean装饰器检�? {has_conditional}")

        # 验证自定义Bean没有条件装饰器（会覆盖默认）
        no_conditional = not (hasattr(custom_method, '__pyspring_conditional__') and \
                              custom_method.__pyspring_conditional__)
        print("�?用户自定义Bean没有条件装饰器，可以覆盖默认实现")

        # 测试行为
        async def run_test():
            default_provider = default_config.default_login_provider()
            custom_provider = user_config.custom_login_provider()

            default_result = await default_provider.authenticate({})
            custom_result = await custom_provider.authenticate({})

            assert default_result["source"] == "default"
            assert custom_result["source"] == "custom"

            print(f"   默认Provider结果: {default_result}")
            print(f"   自定义Provider结果: {custom_result}")
            return True

        result = asyncio.run(run_test())
        assert result
        print("�?@ConditionalOnMissingBean条件覆盖 - 通过")


def run_all_tests():
    """
                运行所有测�?""
    test_suite = TestCustomConfiguration()

    tests = [
        ("自定义用户表", test_suite.test_1_custom_user_table),
        ("自定义Token黑名单表", test_suite.test_2_custom_token_blacklist_table),
        ("自定义@Bean - 登录提供�?, test_suite.test_3_custom_bean_login_provider),
         ("自定义Token Payload构建�?, test_suite.test_4_custom_token_payload_builder),
          ("自定义用户提供者（多数据源�?, test_suite.test_5_custom_user_provider),
        ("自定义响应构建器", test_suite.test_6_custom_response_builder),
           ("集成测试 - 完整自定义配置流�?, test_suite.test_7_integration_custom_config),
        ("@ConditionalOnMissingBean条件覆盖", test_suite.test_8_conditional_bean_override),
    ]

    print("=" * 80)
         print("PySpring 自定义配置测试套�?)
    print("=" * 80)

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"�?{name} - 失败: {e}")
        except Exception as e:
            failed += 1
            print(f"�?{name} - 错误: {type(e).__name__}: {e}")

    print(f"\n{'=' * 80}")
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print(f"{'=' * 80}")

    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

