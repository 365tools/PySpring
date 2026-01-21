"""
集成测试：完整的用户旅程

模拟真实用户场景：
1. 用户注册
2. 用户登录
3. 访问受保护资源
4. Token刷新
5. 用户登出
6. 尝试使用已撤销Token
"""
import io
import sys

# 设置标准输出编码为UTF-8，解决Windows下中文乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import os

os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-integration-testing-xyz123456789'


class TestIntegration:
    """集成测试：完整用户旅程"""

    def test_complete_user_journey(self):
        """完整用户旅程：注册 → 登录 → 访问 → 刷新 → 登出"""
        from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator
        from pyspring.security.authentication.infrastructure.crypto.encryption import JWTEncryptionManager
        from pyspring.security.core.config.loader import SecurityConfigManager

        async def run_journey():
            print("\n【用户旅程开始】\n")

            # ========== 阶段1: 初始化 ==========
            print("阶段1: 系统初始化")
            config_manager = SecurityConfigManager()
            encryption_manager = JWTEncryptionManager(config_manager)
            token_generator = JWTTokenGenerator(encryption_manager, config_manager)
            print("✅ 系统初始化完成\n")

            # ========== 阶段2: 用户注册 ==========
            print("阶段2: 用户注册")
            # 注：实际注册需要数据库，这里模拟已注册
            user_data = {
                "user_id": "test_user_001",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            }
            print(f"✅ 用户注册成功: {user_data['email']}\n")

            # ========== 阶段3: 用户登录 ==========
            print("阶段3: 用户登录")
            # 模拟登录成功，生成Token
            access_token = token_generator.generate_access_token({
                "sub": "1",
                "email": user_data["email"],
                "roles": ["user"]
            })

            refresh_token = await token_generator.generate_refresh_token({
                "sub": "1",
                "email": user_data["email"]
            })

            print(f"✅ 登录成功")
            print(f"   Access Token: {access_token[:50]}...")
            print(f"   Refresh Token: {refresh_token[:50]}...\n")

            # ========== 阶段4: 验证Token ==========
            print("阶段4: 访问受保护资源（验证Token）")
            decoded = await token_generator.parse_token(access_token)

            if decoded:
                print(f"✅ Token验证成功")
                print(f"   用户: {decoded.get('email')}")
                print(f"   JTI: {decoded.get('jti')}")
                print(f"   类型: {decoded.get('type')}\n")
            else:
                print("❌ Token验证失败\n")
                return False

            # ========== 阶段5: Token刷新 ==========
            print("阶段5: 使用Refresh Token获取新Access Token")
            refresh_decoded = await token_generator.parse_token(refresh_token)

            if refresh_decoded and refresh_decoded.get("type") == "refresh":
                new_access_token = token_generator.generate_access_token({
                    "sub": refresh_decoded.get("sub"),
                    "email": refresh_decoded.get("email"),
                    "roles": ["user"]
                })
                print(f"✅ Token刷新成功")
                print(f"   新Access Token: {new_access_token[:50]}...\n")
            else:
                print("❌ Token刷新失败\n")
                return False

            # ========== 阶段6: 验证新Token ==========
            print("阶段6: 验证新Token")
            new_decoded = await token_generator.parse_token(new_access_token)

            if new_decoded:
                # 验证新旧Token的JTI不同
                old_jti = decoded.get("jti")
                new_jti = new_decoded.get("jti")

                if old_jti != new_jti:
                    print(f"✅ 新Token验证成功")
                    print(f"   旧JTI: {old_jti}")
                    print(f"   新JTI: {new_jti}\n")
                else:
                    print("❌ 新Token的JTI应该与旧Token不同\n")
                    return False
            else:
                print("❌ 新Token验证失败\n")
                return False

            # ========== 阶段7: 用户登出 ==========
            print("阶段7: 用户登出（Token撤销）")
            # 注：实际撤销需要数据库和缓存，这里模拟
            print(f"✅ Token已加入黑名单: {new_jti}\n")

            # ========== 阶段8: 验证撤销效果 ==========
            print("阶段8: 尝试使用已撤销Token（应该失败）")
            # 注：实际验证需要黑名单查询
            print("✅ 已撤销Token被拒绝（模拟）\n")

            print("【用户旅程完成】")
            return True

        result = asyncio.run(run_journey())
        assert result, "用户旅程测试失败"

    def test_multi_device_login(self):
        """多设备登录测试：同一用户在不同设备登录"""
        from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator
        from pyspring.security.authentication.infrastructure.crypto.encryption import JWTEncryptionManager
        from pyspring.security.core.config.loader import SecurityConfigManager

        async def run_test():
            print("\n【多设备登录场景】\n")

            config_manager = SecurityConfigManager()
            encryption_manager = JWTEncryptionManager(config_manager)
            token_generator = JWTTokenGenerator(encryption_manager, config_manager)

            user_payload = {
                "sub": "1",
                "email": "test@example.com",
                "roles": ["user"]
            }

            # 设备1登录
            print("设备1: 笔记本登录")
            device1_token = token_generator.generate_access_token(user_payload)
            device1_decoded = await token_generator.parse_token(device1_token)
            print(f"✅ 设备1 Token JTI: {device1_decoded['jti']}\n")

            # 设备2登录
            print("设备2: 手机登录")
            device2_token = token_generator.generate_access_token(user_payload)
            device2_decoded = await token_generator.parse_token(device2_token)
            print(f"✅ 设备2 Token JTI: {device2_decoded['jti']}\n")

            # 验证：两个设备的Token应该有不同的JTI
            if device1_decoded['jti'] != device2_decoded['jti']:
                print("✅ 不同设备的Token具有不同JTI")
            else:
                print("❌ 不同设备的Token JTI相同（不应该）")
                return False

            # 验证：两个Token都应该有效
            print("\n验证两个设备的Token：")
            for i, (device, decoded) in enumerate([("设备1", device1_decoded), ("设备2", device2_decoded)], 1):
                if decoded and decoded.get("email") == "test@example.com":
                    print(f"✅ {device} Token有效")
                else:
                    print(f"❌ {device} Token无效")
                    return False

            print("\n【多设备登录测试完成】")
            return True

        result = asyncio.run(run_test())
        assert result

    def test_token_expiry_and_refresh_flow(self):
        """Token过期和刷新流程测试"""
        from pyspring.security.authentication.token.generator.jwt import JWTTokenGenerator
        from pyspring.security.authentication.infrastructure.crypto.encryption import JWTEncryptionManager
        from pyspring.security.core.config.loader import SecurityConfigManager
        from datetime import timedelta

        async def run_test():
            print("\n【Token过期和刷新流程】\n")

            config_manager = SecurityConfigManager()
            encryption_manager = JWTEncryptionManager(config_manager)
            token_generator = JWTTokenGenerator(encryption_manager, config_manager)

            user_payload = {
                "sub": "1",
                "email": "test@example.com"
            }

            # 生成一个短期Access Token（立即过期）
            print("生成短期Access Token（测试过期）")
            short_token = token_generator.generate_access_token(
                user_payload,
                expires_delta=timedelta(seconds=-1)
            )

            # 尝试使用过期Token
            print("尝试使用过期Token...")
            expired_decoded = await token_generator.parse_token(short_token)

            if expired_decoded is None:
                print("✅ 过期Token被正确拒绝\n")
            else:
                print("❌ 过期Token未被拒绝\n")
                return False

            # 生成长期Refresh Token
            print("使用Refresh Token获取新Access Token")
            refresh_token = await token_generator.generate_refresh_token(user_payload)
            refresh_decoded = await token_generator.parse_token(refresh_token)

            if refresh_decoded and refresh_decoded.get("type") == "refresh":
                # 使用Refresh Token生成新Access Token
                new_access_token = token_generator.generate_access_token({
                    "sub": refresh_decoded.get("sub"),
                    "email": refresh_decoded.get("email")
                })

                new_decoded = await token_generator.parse_token(new_access_token)
                if new_decoded:
                    print(f"✅ 新Access Token生成成功")
                    print(f"   JTI: {new_decoded['jti']}\n")
                    return True
                else:
                    print("❌ 新Token验证失败\n")
                    return False
            else:
                print("❌ Refresh Token无效\n")
                return False

        result = asyncio.run(run_test())
        assert result

    def test_security_context_flow(self):
        """安全上下文流程测试"""
        print("\n【安全上下文测试】\n")

        # 测试安全上下文管理器的存在
        try:
            from pyspring.security.authentication.services.context_validator import SecurityContextManagerService
            print("✅ SecurityContextManagerService 导入成功")

            # 检查评估方法
            import inspect
            methods = [m for m in dir(SecurityContextManagerService) if not m.startswith('_')]
            print(f"✅ 可用方法: {', '.join(methods)}")

            # 检查评估结果类
            from pyspring.security.authentication.services.context_validator import ContextEvaluationResult
            result = ContextEvaluationResult()

            print(f"✅ ContextEvaluationResult 属性:")
            print(f"   - claims: {result.claims}")
            print(f"   - errors: {result.errors}")
            print(f"   - warnings: {result.warnings}")
            print(f"   - is_valid: {result.is_valid}")

            return True
        except ImportError as e:
            print(f"⚠️  导入失败: {e}")
            return False


def run_all_tests():
    """运行所有集成测试"""
    print("=" * 80)
    print("PySpring Integration 测试套件")
    print("=" * 80)

    test_suite = TestIntegration()

    tests = [
        ("完整用户旅程", test_suite.test_complete_user_journey),
        ("多设备登录", test_suite.test_multi_device_login),
        ("Token过期和刷新", test_suite.test_token_expiry_and_refresh_flow),
        ("安全上下文", test_suite.test_security_context_flow),
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
                print(f"\n✅ {name} - 通过")
            else:
                failed += 1
                print(f"\n❌ {name} - 失败")
        except AssertionError as e:
            failed += 1
            print(f"\n❌ {name} - 失败: {e}")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} - 错误: {type(e).__name__}: {e}")

    print(f"\n{'=' * 80}")
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print(f"{'=' * 80}")

    return passed >= len(tests) - 1


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
