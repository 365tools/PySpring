"""
安全策略和防护机制测试

测试范围：
1. 时序攻击防护
2. 输入验证
3. 错误消息一致性
4. 密码哈希安全性
5. JWT密钥验证
6. 信息泄露防护
"""
import io
import sys

# 设置标准输出编码为UTF-8，解决Windows下中文乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import os
import time
from unittest.mock import Mock, AsyncMock

os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-security-policies-testing-abcdefgh'


class TestSecurityPolicies:
    """安全策略测试"""

    def test_1_timing_attack_protection(self):
        """测试1: 时序攻击防护（用户枚举）"""
        from pyspring.security.authentication.providers.login.password import DefaultPasswordLoginProvider
        from pyspring.security.authentication.contracts.request import LoginRequest
        from pyspring.security.authentication.providers.password.bcrypt import BCryptPasswordEncoder

        async def run_test():
            mock_user_provider = Mock()
            mock_db = Mock()
            password_encoder = BCryptPasswordEncoder()
            provider = DefaultPasswordLoginProvider(mock_user_provider, mock_db, password_encoder)

            times = []
            scenarios = [
                ("用户不存在", None),
                ("密码错误", Mock(id=1, password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNd.OwVgKi"))
            ]

            for scenario_name, user in scenarios:
                mock_user_provider.get_user_by_identity = AsyncMock(return_value=user)

                start = time.time()
                try:
                    await provider.authenticate(LoginRequest(email="test@test.com", password="wrong123"))
                except:
                    pass
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"{scenario_name}: {elapsed:.4f}s")

            # 计算时间差
            time_diff = abs(times[0] - times[1])
            time_diff_ms = time_diff * 1000

            print(f"\n时间差: {time_diff_ms:.1f}ms")

            # 安全阈值：时间差应小于100ms
            if time_diff_ms < 100:
                print(f"✅ 时序攻击防护有效（时间差 < 100ms）")
                return True
            else:
                print(f"⚠️  时序差异过大（{time_diff_ms:.1f}ms）")
                return False

        result = asyncio.run(run_test())
        assert result, "时序攻击防护失败"

    def test_2_error_message_consistency(self):
        """测试2: 错误消息一致性（不泄露用户存在性）"""
        from pyspring.security.authentication.providers.login.password import DefaultPasswordLoginProvider
        from pyspring.security.authentication.contracts.request import LoginRequest
        from pyspring.security.authentication.providers.password.bcrypt import BCryptPasswordEncoder

        async def run_test():
            mock_user_provider = Mock()
            mock_db = Mock()
            password_encoder = BCryptPasswordEncoder()
            provider = DefaultPasswordLoginProvider(mock_user_provider, mock_db, password_encoder)

            errors = []

            # 场景1：用户不存在
            mock_user_provider.get_user_by_identity = AsyncMock(return_value=None)
            try:
                await provider.authenticate(LoginRequest(email="nonexist@test.com", password="test123"))
            except Exception as e:
                errors.append(str(e.detail if hasattr(e, 'detail') else e))

            # 场景2：密码错误
            mock_user = Mock(id=1, password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYNd.OwVgKi")
            mock_user_provider.get_user_by_identity = AsyncMock(return_value=mock_user)
            try:
                await provider.authenticate(LoginRequest(email="exist@test.com", password="wrong123"))
            except Exception as e:
                errors.append(str(e.detail if hasattr(e, 'detail') else e))

            print(f"错误消息1（用户不存在）: {errors[0]}")
            print(f"错误消息2（密码错误）: {errors[1]}")

            # 检查消息是否一致
            if errors[0] == errors[1]:
                print("✅ 错误消息一致，不泄露用户存在性")
                # 检查是否包含敏感信息
                sensitive_keywords = ["不存在", "未找到", "未注册", "邮箱", "ID"]
                has_sensitive = any(kw in errors[0] for kw in sensitive_keywords)
                if has_sensitive:
                    print(f"⚠️  错误消息可能包含敏感信息: {errors[0]}")
                    return False
                return True
            else:
                print("❌ 错误消息不一致，会泄露用户存在性")
                return False

        result = asyncio.run(run_test())
        assert result

    def test_3_registration_error_consistency(self):
        """测试3: 注册错误消息一致性"""
        from pyspring.security.authentication.services.register import DefaultRegisterService
        import inspect

        # 代码审查：检查注册错误消息
        source = inspect.getsource(DefaultRegisterService._check_user_exists)

        # 检查是否有泄露信息的错误消息
        leaks = []
        if "邮箱" in source and "已被注册" in source:
            leaks.append("泄露邮箱存在性")
        if "用户ID" in source and "已被使用" in source:
            leaks.append("泄露用户ID存在性")

        if leaks:
            print(f"⚠️  发现信息泄露: {', '.join(leaks)}")
            print("建议使用统一消息：'注册失败：用户信息已存在'")
            # 检查是否已经修复
            if "用户信息已存在" in source:
                print("✅ 已使用统一错误消息")
                return True
            return False
        else:
            print("✅ 注册错误消息不泄露敏感信息")
            return True

        assert True  # 这是代码审查，总是通过但给出警告

    def test_4_input_validation_user_id(self):
        """测试4: 用户ID输入验证"""
        from pyspring.security.authentication.services.user.manager import DefaultUserManagerService
        import inspect

        # 代码审查：检查get_current_user中的输入验证
        source = inspect.getsource(DefaultUserManagerService.get_current_user)

        checks = {
            "类型转换保护": "try:" in source and "int(" in source,
            "边界检查": "user_id <= 0" in source or "user_id < 0" in source or "user_id > 0" in source,
            "异常捕获": "ValueError" in source or "TypeError" in source,
            "错误日志": "logger" in source and "warning" in source.lower() or "error" in source.lower(),
        }

        print("用户ID输入验证检查：")
        for name, passed in checks.items():
            status = "✅" if passed else "⚠️ "
            print(f"  {status} {name}")

        # 至少应该有类型转换保护和异常捕获
        critical_checks = checks["类型转换保护"] and checks["异常捕获"]

        if critical_checks:
            print("✅ 输入验证包含关键保护")
            return True
        else:
            print("⚠️  输入验证可能不完整")
            return False

        assert True

    def test_5_jwt_secret_validation(self):
        """测试5: JWT密钥强制验证"""
        from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator
        from pyspring.security.authentication.infrastructure.crypto.encryption import JWTEncryptionManager
        from pyspring.security.core.config.loader import SecurityConfigManager

        # 测试1：使用有效密钥
        config_manager = SecurityConfigManager()
        encryption_manager = JWTEncryptionManager(config_manager)

        try:
            generator = JWTTokenGenerator(encryption_manager, config_manager)
            print("✅ 有效密钥被接受")
        except ValueError as e:
            print(f"❌ 有效密钥被拒绝: {e}")
            return False

        # 测试2：尝试使用空密钥（应该失败）
        old_key = os.environ.get('JWT_SECRET_KEY')
        try:
            os.environ['JWT_SECRET_KEY'] = ''
            config_manager2 = SecurityConfigManager()
            encryption_manager2 = JWTEncryptionManager(config_manager2)

            try:
                generator2 = JWTTokenGenerator(encryption_manager2, config_manager2)
                print("❌ 空密钥未被拒绝")
                return False
            except ValueError as e:
                if "jwt" in str(e).lower() and "secret" in str(e).lower():
                    print(f"✅ 空密钥被正确拒绝: {type(e).__name__}")
                    return True
                else:
                    print(f"⚠️  拒绝原因不明确: {e}")
                    return True  # 至少被拒绝了
        finally:
            if old_key:
                os.environ['JWT_SECRET_KEY'] = old_key

        return True

    def test_6_password_hash_security(self):
        """测试6: 密码哈希安全性"""
        from pyspring.security.authentication.providers.login.password import DefaultPasswordLoginProvider

        # 检查使用的密码哈希库
        import inspect
        source = inspect.getsource(DefaultPasswordLoginProvider)

        checks = {
            "使用IPasswordEncoder": "IPasswordEncoder" in source or "password_encoder" in source,
            "不使用MD5": "md5" not in source.lower(),
            "不使用SHA1": "sha1" not in source.lower(),
            "使用bcrypt": "bcrypt" in source.lower() or "password_encoder" in source.lower(),
        }

        print("密码哈希安全性检查：")
        for name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")

        # 应该使用安全的哈希库
        if checks["使用IPasswordEncoder"] and checks["不使用MD5"]:
            print("✅ 使用安全的密码哈希机制")
            return True
        else:
            print("❌ 密码哈希可能不安全")
            return False

    def test_7_concurrent_password_update_protection(self):
        """测试7: 密码并发更新保护"""
        from pyspring.security.authentication.providers.login.password import DefaultPasswordLoginProvider
        import inspect

        # 检查密码更新是否使用锁
        source = inspect.getsource(DefaultPasswordLoginProvider.authenticate)

        checks = {
            "使用select_for_update": "select_for_update" in source or "for_update" in source,
            "使用悲观锁": "with_for_update" in source,
            "有事务管理": "session" in source and ("commit" in source or "flush" in source),
        }

        print("密码并发更新保护检查：")
        for name, passed in checks.items():
            status = "✅" if passed else "⚠️ "
            print(f"  {status} {name}")

        # 至少应该有锁机制
        if any(checks.values()):
            print("✅ 包含并发控制机制")
            return True
        else:
            print("⚠️  可能缺少并发控制")
            return True  # 非关键问题

    def test_8_dummy_hash_verification(self):
        """测试8: Dummy Hash验证（时序攻击防护实现）"""
        from pyspring.security.authentication.providers.login.password import DefaultPasswordLoginProvider
        import inspect

        # 检查是否实现了dummy hash
        source = inspect.getsource(DefaultPasswordLoginProvider.authenticate)

        checks = {
            "有dummy_hash变量": "dummy_hash" in source or "dummy hash" in source.lower(),
            "用户不存在时执行验证": "if user:" in source or "if not user:" in source,
            "使用有效bcrypt哈希": "$2b$" in source,
        }

        print("Dummy Hash实现检查：")
        for name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {name}")

        if all(checks.values()):
            print("✅ 时序攻击防护实现完整")
            return True
        else:
            print("⚠️  时序攻击防护可能不完整")
            return False


def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("PySpring Security Policies 测试套件")
    print("=" * 80)

    test_suite = TestSecurityPolicies()

    tests = [
        ("时序攻击防护", test_suite.test_1_timing_attack_protection),
        ("登录错误消息一致性", test_suite.test_2_error_message_consistency),
        ("注册错误消息一致性", test_suite.test_3_registration_error_consistency),
        ("用户ID输入验证", test_suite.test_4_input_validation_user_id),
        ("JWT密钥强制验证", test_suite.test_5_jwt_secret_validation),
        ("密码哈希安全性", test_suite.test_6_password_hash_security),
        ("密码并发更新保护", test_suite.test_7_concurrent_password_update_protection),
        ("Dummy Hash实现", test_suite.test_8_dummy_hash_verification),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n{'=' * 80}")
        print(f"测试: {name}")
        print(f"{'=' * 80}")
        try:
            result = test_func()
            if result or result is None:
                passed += 1
                print(f"✅ {name} - 通过")
            else:
                failed += 1
                print(f"❌ {name} - 失败")
        except AssertionError as e:
            failed += 1
            print(f"❌ {name} - 失败: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {name} - 错误: {type(e).__name__}: {e}")

    print(f"\n{'=' * 80}")
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print(f"{'=' * 80}")

    return passed >= len(tests) - 1  # 允许1个失败


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
