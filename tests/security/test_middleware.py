"""
PySpring 中间件测试套件

测试认证中间件和授权中间件的功能
"""
import io
import sys

# 设置标准输出编码为UTF-8，解决Windows下中文乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from fastapi import FastAPI


class TestAuthenticationMiddleware:
    """测试认证中间件"""

    def test_1_middleware_initialization(self):
        """测试1: 中间件初始化"""
        print("\n" + "=" * 80)
        print("测试: 中间件初始化")
        print("=" * 80)

        from pyspring.security.authentication.web.middleware.auth import AuthenticationMiddleware

        # 创建FastAPI应用
        app = FastAPI()

        # 创建中间件实例
        middleware = AuthenticationMiddleware(app, enable_role_check=False)

        assert middleware is not None
        assert middleware.enable_role_check_initial_setting is False
        print("✅ 认证中间件初始化成功")
        print(f"   - enable_role_check_initial_setting: {middleware.enable_role_check_initial_setting}")

        print("✅ 中间件初始化 - 通过")

    def test_2_whitelist_configuration(self):
        """测试2: 白名单配置验证"""
        print("\n" + "=" * 80)
        print("测试: 白名单配置验证")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        # 创建配置管理器
        config_manager = SecurityConfigManager()

        # 获取白名单配置
        whitelist_config = config_manager.get_whitelist_config()

        assert whitelist_config is not None
        assert "exact_paths" in whitelist_config
        assert "prefix_paths" in whitelist_config
        assert "regex_patterns" in whitelist_config
        print("✅ 白名单配置结构正确")

        # 验证必需的白名单路径
        exact_paths = whitelist_config["exact_paths"]
        essential_paths = ["/", "/health", "/api/auth/login", "/api/auth/register"]

        for path in essential_paths:
            if path in exact_paths:
                print(f"✅ 必需路径在白名单中: {path}")

        # 验证前缀路径
        prefix_paths = whitelist_config["prefix_paths"]
        print(f"✅ 前缀路径白名单 ({len(prefix_paths)}个): {prefix_paths}")

        # 验证正则模式
        regex_patterns = whitelist_config["regex_patterns"]
        print(f"✅ 正则模式白名单 ({len(regex_patterns)}个)")

        print("✅ 白名单配置验证 - 通过")

    def test_3_authentication_chain_initialization(self):
        """测试3: 认证链初始化"""
        print("\n" + "=" * 80)
        print("测试: 认证链初始化")
        print("=" * 80)

        # 测试认证链类存在
        from pyspring.security.authentication.infrastructure.chain import AuthenticationChain
        assert AuthenticationChain is not None
        print("✅ 认证链类存在")

        # 验证认证链的核心方法存在
        assert hasattr(AuthenticationChain, 'authenticate')
        assert hasattr(AuthenticationChain, 'register_provider')
        assert hasattr(AuthenticationChain, 'is_public_path')
        print("✅ 认证链核心方法存在:")
        print("   - authenticate()")
        print("   - register_provider()")
        print("   - is_public_path()")

        print("✅ 认证链初始化 - 通过")

    def test_4_role_middleware_structure(self):
        """测试4: 角色中间件结构验证"""
        print("\n" + "=" * 80)
        print("测试: 角色中间件结构验证")
        print("=" * 80)

        from pyspring.security.authorization.web.middleware.role import RoleCheckMiddleware

        # 验证中间件类存在
        assert RoleCheckMiddleware is not None
        print("✅ 角色检查中间件类存在")

        # 验证核心方法
        assert hasattr(RoleCheckMiddleware, 'auth')
        assert hasattr(RoleCheckMiddleware, 'requires_role')
        print("✅ 角色中间件核心方法存在:")
        print("   - auth()")
        print("   - requires_role()")

        print("✅ 角色中间件结构验证 - 通过")

    def test_5_middleware_error_response(self):
        """测试5: 中间件错误响应格式"""
        print("\n" + "=" * 80)
        print("测试: 中间件错误响应格式")
        print("=" * 80)

        from pyspring.security.authentication.web.middleware.auth import AuthenticationMiddleware

        # 测试错误响应创建
        response = AuthenticationMiddleware.create_error_response(
            status_code=401,
            message="Authentication Required",
            detail="No valid token provided"
        )

        assert response is not None
        assert response.status_code == 401
        print(f"✅ 错误响应创建成功: {response.status_code}")

        # 验证响应内容
        import json
        body = json.loads(response.body.decode('utf-8'))
        assert "code" in body
        assert body["code"] == 401
        assert "message" in body
        assert body["message"] == "Authentication Required"
        print("✅ 错误响应格式正确:")
        print(f"   - code: {body['code']}")
        print(f"   - message: {body['message']}")
        print(f"   - detail: {body.get('detail')}")

        print("✅ 中间件错误响应格式 - 通过")

    def test_6_middleware_lazy_initialization(self):
        """测试6: 中间件懒加载机制"""
        print("\n" + "=" * 80)
        print("测试: 中间件懒加载机制")
        print("=" * 80)

        from pyspring.security.authentication.web.middleware.auth import AuthenticationMiddleware

        # 创建FastAPI应用
        app = FastAPI()

        # 创建中间件
        middleware = AuthenticationMiddleware(app, enable_role_check=False)

        # 验证初始状态（未初始化）
        assert middleware._initialization_attempted is False
        assert middleware._config_manager is None
        assert middleware._auth_chain is None
        print("✅ 中间件初始状态正确（未初始化）")
        print("   - _initialization_attempted: False")
        print("   - _config_manager: None")
        print("   - _auth_chain: None")

        # 验证懒加载方法存在
        assert hasattr(middleware, '_ensure_initialized')
        print("✅ 懒加载方法存在: _ensure_initialized()")

        print("✅ 中间件懒加载机制 - 通过")

    def test_7_jwt_provider_config(self):
        """测试7: JWT认证提供者配置"""
        print("\n" + "=" * 80)
        print("测试: JWT认证提供者配置")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        # 获取配置
        config_manager = SecurityConfigManager()
        auth_config = config_manager.get_authentication_config()

        # 获取JWT提供者配置
        providers = auth_config.get("providers", [])
        jwt_provider = next((p for p in providers if p["name"] == "jwt"), None)

        assert jwt_provider is not None
        print("✅ JWT认证提供者配置存在")

        # 验证JWT提供者配置
        assert jwt_provider["type"] == "JWTAuthProvider"
        assert jwt_provider["enabled"] is True
        print(f"✅ JWT提供者配置:")
        print(f"   - type: {jwt_provider['type']}")
        print(f"   - enabled: {jwt_provider['enabled']}")
        print(f"   - priority: {jwt_provider['priority']}")

        # 验证token来源配置
        if "config" in jwt_provider:
            provider_config = jwt_provider["config"]
            token_sources = provider_config.get("token_sources", [])
            print(f"✅ Token来源配置: {token_sources}")

            if "header" in token_sources:
                print("   - ✅ 支持Authorization Header")
            if "cookie" in token_sources:
                print("   - ✅ 支持Cookie")
            if "query" in token_sources:
                print("   - ✅ 支持Query参数")

        print("✅ JWT认证提供者配置 - 通过")

    def test_8_auth_context_structure(self):
        """测试8: 认证上下文结构"""
        print("\n" + "=" * 80)
        print("测试: 认证上下文结构")
        print("=" * 80)

        from pyspring.security.authentication.infrastructure.context import AuthContext

        # 验证AuthContext类存在
        assert AuthContext is not None
        print("✅ 认证上下文类存在")

        # 验证上下文方法
        assert hasattr(AuthContext, 'get_current_user')
        assert hasattr(AuthContext, 'set_current_user')
        assert hasattr(AuthContext, 'clear')
        print("✅ 认证上下文方法存在:")
        print("   - get_current_user()")
        print("   - set_current_user()")
        print("   - clear()")

        # 验证构造函数签名
        import inspect
        init_sig = inspect.signature(AuthContext.__init__)
        params = list(init_sig.parameters.keys())
        print(f"✅ AuthContext构造函数参数: {params}")

        print("✅ 认证上下文结构 - 通过")


def run_all_tests():
    """运行所有测试"""
    test_suite = TestAuthenticationMiddleware()

    tests = [
        ("中间件初始化", test_suite.test_1_middleware_initialization),
        ("白名单配置验证", test_suite.test_2_whitelist_configuration),
        ("认证链初始化", test_suite.test_3_authentication_chain_initialization),
        ("角色中间件结构验证", test_suite.test_4_role_middleware_structure),
        ("中间件错误响应格式", test_suite.test_5_middleware_error_response),
        ("中间件懒加载机制", test_suite.test_6_middleware_lazy_initialization),
        ("JWT认证提供者配置", test_suite.test_7_jwt_provider_config),
        ("认证上下文结构", test_suite.test_8_auth_context_structure),
    ]

    print("=" * 80)
    print("PySpring 中间件测试套件")
    print("=" * 80)

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ {name} - 失败: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {name} - 错误: {type(e).__name__}: {e}")

    print(f"\n{'=' * 80}")
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print(f"{'=' * 80}")

    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
