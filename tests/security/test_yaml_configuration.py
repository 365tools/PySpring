"""
PySpring YAML配置加载测试套件

测试YAML配置文件的加载、解析、环境变量覆盖等功能
"""
import io
import sys

# 设置标准输出编码为UTF-8，解决Windows下中文乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import os
import tempfile
from unittest.mock import patch
import yaml


class TestYAMLConfigLoading:
    """测试YAML配置加载"""

    def test_1_security_config_loading(self):
        """测试1: security.yaml配置加载"""
        print("\n" + "=" * 80)
        print("测试: security.yaml配置加载")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        # 创建配置管理器实例（会自动加载配置）
        config_manager = SecurityConfigManager()

        # 验证配置已加载
        assert config_manager._config is not None
        print("✅ 配置已加载")

        # 验证authentication配置
        auth_config = config_manager.get_authentication_config()
        assert auth_config is not None
        assert "jwt" in auth_config
        print(f"✅ authentication配置存在")
        print(f"   - enabled: {auth_config.get('enabled')}")
        print(f"   - jwt.algorithm: {auth_config['jwt'].get('algorithm')}")

        # 验证authorization配置
        authz_config = config_manager.get_authorization_config()
        assert authz_config is not None
        print(f"✅ authorization配置存在")
        print(f"   - enabled: {authz_config.get('enabled')}")

        # 验证whitelist配置
        whitelist_config = config_manager.get_whitelist_config()
        assert whitelist_config is not None
        exact_paths = whitelist_config.get("exact_paths", [])
        assert len(exact_paths) > 0
        print(f"✅ whitelist配置存在 ({len(exact_paths)}个精确路径)")
        print(f"   示例: {exact_paths[:3]}")

        print("✅ security.yaml配置加载 - 通过")

    def test_2_jwt_config_structure(self):
        """测试2: JWT配置结构验证"""
        print("\n" + "=" * 80)
        print("测试: JWT配置结构验证")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        config_manager = SecurityConfigManager()
        jwt_config = config_manager.get_jwt_config()

        # 验证必需字段
        required_fields = ["algorithm", "access_token_expire", "refresh_token_expire"]
        for field in required_fields:
            assert field in jwt_config, f"JWT配置缺少必需字段: {field}"
            print(f"✅ {field}: {jwt_config[field]}")

        # 验证算法值
        assert jwt_config["algorithm"] in ["HS256", "HS384", "HS512", "RS256"]
        print(f"✅ 使用支持的JWT算法: {jwt_config['algorithm']}")

        # 验证过期时间是合理的
        assert jwt_config["access_token_expire"] > 0
        assert jwt_config["refresh_token_expire"] > jwt_config["access_token_expire"]
        print(f"✅ Token过期时间合理:")
        print(f"   - Access Token: {jwt_config['access_token_expire']}秒 ({jwt_config['access_token_expire'] // 3600}小时)")
        print(f"   - Refresh Token: {jwt_config['refresh_token_expire']}秒 ({jwt_config['refresh_token_expire'] // 86400}天)")

        print("✅ JWT配置结构验证 - 通过")

    def test_3_env_variable_override(self):
        """测试3: 环境变量覆盖配置"""
        print("\n" + "=" * 80)
        print("测试: 环境变量覆盖配置")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        # 设置测试环境变量
        test_secret = "test-secret-key-from-env-12345678901234567890"
        test_algorithm = "HS512"
        test_expire = "7200"

        with patch.dict(os.environ, {
            'JWT_SECRET_KEY': test_secret,
            'JWT_ALGORITHM': test_algorithm,
            'ACCESS_TOKEN_EXPIRE': test_expire
        }):
            # 创建新的配置管理器（会应用环境变量）
            config_manager = SecurityConfigManager()
            jwt_config = config_manager.get_jwt_config()

            # 验证环境变量已覆盖配置
            assert jwt_config["secret_key"] == test_secret
            print(f"✅ JWT_SECRET_KEY已从环境变量覆盖")
            print(f"   值: {test_secret[:20]}...")

            assert jwt_config["algorithm"] == test_algorithm
            print(f"✅ JWT_ALGORITHM已从环境变量覆盖: {test_algorithm}")

            assert jwt_config["access_token_expire"] == int(test_expire)
            print(f"✅ ACCESS_TOKEN_EXPIRE已从环境变量覆盖: {test_expire}秒")

        print("✅ 环境变量覆盖配置 - 通过")

    def test_4_whitelist_configuration(self):
        """测试4: 白名单配置验证"""
        print("\n" + "=" * 80)
        print("测试: 白名单配置验证")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        config_manager = SecurityConfigManager()

        # 获取白名单配置
        auth_config = config_manager.get_authentication_config()
        whitelist_config = auth_config.get("whitelist", {})

        # 验证白名单类型
        assert "exact_paths" in whitelist_config
        assert "prefix_paths" in whitelist_config
        assert "regex_patterns" in whitelist_config
        print("✅ 白名单包含三种类型:")
        print("   - exact_paths (精确匹配)")
        print("   - prefix_paths (前缀匹配)")
        print("   - regex_patterns (正则匹配)")

        # 验证常见路径在白名单中
        exact_paths = whitelist_config["exact_paths"]
        essential_paths = ["/api/auth/login", "/api/auth/register", "/health"]
        for path in essential_paths:
            assert path in exact_paths, f"必需路径未在白名单中: {path}"
            print(f"✅ 必需路径已配置: {path}")

        # 验证前缀路径
        prefix_paths = whitelist_config["prefix_paths"]
        assert len(prefix_paths) > 0
        print(f"✅ 前缀路径白名单: {prefix_paths}")

        print("✅ 白名单配置验证 - 通过")

    def test_5_providers_configuration(self):
        """测试5: 认证提供者配置"""
        print("\n" + "=" * 80)
        print("测试: 认证提供者配置")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        config_manager = SecurityConfigManager()
        auth_config = config_manager.get_authentication_config()

        # 获取提供者配置
        providers = auth_config.get("providers", [])
        assert len(providers) > 0, "至少应该有一个认证提供者配置"
        print(f"✅ 配置了 {len(providers)} 个认证提供者")

        # 验证JWT提供者
        jwt_provider = next((p for p in providers if p["name"] == "jwt"), None)
        assert jwt_provider is not None, "必须配置JWT认证提供者"
        assert jwt_provider["type"] == "JWTAuthProvider"
        assert jwt_provider["enabled"] is True
        print("✅ JWT认证提供者配置:")
        print(f"   - name: {jwt_provider['name']}")
        print(f"   - type: {jwt_provider['type']}")
        print(f"   - enabled: {jwt_provider['enabled']}")
        print(f"   - priority: {jwt_provider['priority']}")

        # 验证提供者的config子配置
        if "config" in jwt_provider:
            provider_config = jwt_provider["config"]
            print(f"✅ JWT提供者详细配置:")
            print(f"   - token_sources: {provider_config.get('token_sources')}")
            print(f"   - token_prefix: {provider_config.get('token_prefix')}")

        print("✅ 认证提供者配置 - 通过")

    def test_6_authorization_configuration(self):
        """测试6: 授权配置验证"""
        print("\n" + "=" * 80)
        print("测试: 授权配置验证")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        config_manager = SecurityConfigManager()
        authz_config = config_manager.get_authorization_config()

        # 验证基本字段
        assert "enabled" in authz_config
        print(f"✅ 授权功能启用状态: {authz_config['enabled']}")

        # 验证角色映射配置
        if "role_mappings" in authz_config:
            role_mappings = authz_config["role_mappings"]
            print(f"✅ 角色映射配置存在 ({len(role_mappings)}个规则)")
            if role_mappings:
                # 显示前3个映射
                for i, (path, roles) in enumerate(list(role_mappings.items())[:3]):
                    print(f"   [{i + 1}] {path} -> {roles}")

        # 验证角色层级配置
        if "role_hierarchy" in authz_config:
            role_hierarchy = authz_config["role_hierarchy"]
            print(f"✅ 角色层级配置存在")
            if role_hierarchy:
                for parent, children in list(role_hierarchy.items())[:3]:
                    print(f"   {parent} > {children}")

        print("✅ 授权配置验证 - 通过")

    def test_7_jwt_encryption_configuration(self):
        """测试7: JWT加密配置"""
        print("\n" + "=" * 80)
        print("测试: JWT加密配置")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        config_manager = SecurityConfigManager()
        jwt_config = config_manager.get_jwt_config()

        # 验证加密配置
        if "encryption" in jwt_config:
            encryption_config = jwt_config["encryption"]
            print("✅ JWT加密配置存在:")
            print(f"   - enabled: {encryption_config.get('enabled', False)}")
            print(f"   - algorithm: {encryption_config.get('algorithm', 'Fernet')}")

            # 验证加密算法
            if encryption_config.get('enabled'):
                algorithm = encryption_config.get('algorithm')
                assert algorithm in ["Fernet", "AES-GCM"], f"不支持的加密算法: {algorithm}"
                print(f"✅ 使用支持的加密算法: {algorithm}")
        else:
            print("⚠️  JWT加密配置不存在（使用默认禁用）")

        print("✅ JWT加密配置 - 通过")

    def test_8_config_file_not_found_fallback(self):
        """测试8: 配置文件不存在时的降级策略"""
        print("\n" + "=" * 80)
        print("测试: 配置文件不存在时的降级策略")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        # 在没有配置文件的临时目录中创建配置管理器
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # 创建配置管理器（应该使用默认配置）
                config_manager = SecurityConfigManager()

                # 验证使用了默认配置
                assert config_manager._config is not None
                print("✅ 配置文件不存在时，使用默认配置")

                # 验证默认配置包含必需项
                jwt_config = config_manager.get_jwt_config()
                assert jwt_config is not None
                assert "algorithm" in jwt_config
                assert jwt_config["algorithm"] == "HS256"
                print(f"✅ 默认JWT算法: {jwt_config['algorithm']}")

                auth_config = config_manager.get_authentication_config()
                assert auth_config.get("enabled") is True
                print("✅ 默认启用认证")

            finally:
                os.chdir(original_cwd)

        print("✅ 配置文件不存在时的降级策略 - 通过")

    def test_9_custom_yaml_structure(self):
        """测试9: 自定义YAML配置结构验证"""
        print("\n" + "=" * 80)
        print("测试: 自定义YAML配置结构验证")
        print("=" * 80)

        # 读取实际的security.yaml文件
        from pyspring.utils.config.finder import find_config_file

        config_file = find_config_file('security.yaml')
        if not config_file:
            print("⚠️  未找到security.yaml配置文件，跳过此测试")
            return

        # 解析YAML
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 验证顶层结构
        expected_sections = ["authentication", "authorization"]
        for section in expected_sections:
            assert section in config, f"配置缺少必需的顶层节点: {section}"
            print(f"✅ 顶层节点存在: {section}")

        # 验证authentication子节点
        auth = config["authentication"]
        assert "enabled" in auth
        assert "jwt" in auth
        assert "providers" in auth
        assert "whitelist" in auth
        print("✅ authentication包含所有必需子节点:")
        print(f"   - enabled, jwt, providers, whitelist")

        # 验证jwt子节点
        jwt = auth["jwt"]
        jwt_fields = ["algorithm", "access_token_expire", "refresh_token_expire"]
        for field in jwt_fields:
            assert field in jwt, f"JWT配置缺少字段: {field}"
        print(f"✅ jwt包含必需字段: {', '.join(jwt_fields)}")

        # 验证providers是列表
        assert isinstance(auth["providers"], list)
        assert len(auth["providers"]) > 0
        print(f"✅ providers是列表，包含{len(auth['providers'])}个提供者")

        # 验证whitelist结构
        whitelist = auth["whitelist"]
        whitelist_types = ["exact_paths", "prefix_paths", "regex_patterns"]
        for wl_type in whitelist_types:
            assert wl_type in whitelist
            assert isinstance(whitelist[wl_type], list)
        print(f"✅ whitelist包含所有类型: {', '.join(whitelist_types)}")

        print("✅ 自定义YAML配置结构验证 - 通过")

    def test_10_config_compatibility_check(self):
        """测试10: 配置与框架设计兼容性检查"""
        print("\n" + "=" * 80)
        print("测试: 配置与框架设计兼容性检查")
        print("=" * 80)

        from pyspring.security.core.config.loader import SecurityConfigManager

        config_manager = SecurityConfigManager()

        # 1. 验证配置可以被SecurityConfigManager正确解析
        jwt_config = config_manager.get_jwt_config()
        auth_config = config_manager.get_authentication_config()
        authz_config = config_manager.get_authorization_config()

        assert jwt_config is not None
        assert auth_config is not None
        assert authz_config is not None
        print("✅ 配置可以被SecurityConfigManager正确解析")

        # 2. 验证JWT配置字段与JWTTokenGenerator期望一致
        required_jwt_fields = ["secret_key", "algorithm", "access_token_expire", "refresh_token_expire"]
        for field in required_jwt_fields:
            assert field in jwt_config, f"JWT配置缺少JWTTokenGenerator所需字段: {field}"
        print("✅ JWT配置字段与JWTTokenGenerator期望一致")

        # 3. 验证白名单配置与中间件期望一致
        whitelist_config = config_manager.get_whitelist_config()
        assert isinstance(whitelist_config, dict)
        assert len(whitelist_config.get("exact_paths", [])) > 0
        print(f"✅ 白名单配置与中间件期望一致")

        # 4. 验证认证提供者配置结构
        providers = auth_config.get("providers", [])
        for provider in providers:
            assert "name" in provider
            assert "type" in provider
            assert "enabled" in provider
            print(f"✅ 提供者 '{provider['name']}' 配置结构正确")

        # 5. 验证配置值类型正确
        assert isinstance(jwt_config["access_token_expire"], int)
        assert isinstance(jwt_config["refresh_token_expire"], int)
        assert isinstance(auth_config["enabled"], bool)
        assert isinstance(authz_config["enabled"], bool)
        print("✅ 所有配置值类型正确")

        # 6. 验证环境变量优先级
        with patch.dict(os.environ, {'JWT_SECRET_KEY': 'test-override'}):
            new_config_manager = SecurityConfigManager()
            new_jwt_config = new_config_manager.get_jwt_config()
            assert new_jwt_config["secret_key"] == 'test-override'
        print("✅ 环境变量优先级正确（环境变量 > YAML文件）")

        print("✅ 配置与框架设计兼容性检查 - 通过")


def run_all_tests():
    """运行所有测试"""
    test_suite = TestYAMLConfigLoading()

    tests = [
        ("security.yaml配置加载", test_suite.test_1_security_config_loading),
        ("JWT配置结构验证", test_suite.test_2_jwt_config_structure),
        ("环境变量覆盖配置", test_suite.test_3_env_variable_override),
        ("白名单配置验证", test_suite.test_4_whitelist_configuration),
        ("认证提供者配置", test_suite.test_5_providers_configuration),
        ("授权配置验证", test_suite.test_6_authorization_configuration),
        ("JWT加密配置", test_suite.test_7_jwt_encryption_configuration),
        ("配置文件不存在时的降级策略", test_suite.test_8_config_file_not_found_fallback),
        ("自定义YAML配置结构验证", test_suite.test_9_custom_yaml_structure),
        ("配置与框架设计兼容性检查", test_suite.test_10_config_compatibility_check),
    ]

    print("=" * 80)
    print("PySpring YAML配置加载测试套件")
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
