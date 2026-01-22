"""
IPasswordEncoder和BCryptPasswordEncoder单元测试

测试内容：
1. IPasswordEncoder接口定义
2. BCryptPasswordEncoder基本功能
3. 密码编码安全性
4. 密码验证准确性
5. 空密码和特殊字符处理
"""
import pytest
from pyspring.security.authentication.contracts.password import IPasswordEncoder
from pyspring.security.authentication.providers.password.bcrypt import BCryptPasswordEncoder


class TestIPasswordEncoder:
    """IPasswordEncoder接口测试"""

    def test_interface_definition(self):
        """测试接口定义完整性"""
        assert hasattr(IPasswordEncoder, 'encode')
        assert hasattr(IPasswordEncoder, 'verify')
        print("✅ IPasswordEncoder接口定义完整")

    def test_interface_is_abstract(self):
        """测试接口不能直接实例化"""
        try:
            encoder = IPasswordEncoder()
            pytest.fail("IPasswordEncoder不应该能够直接实例化")
        except TypeError:
            print("✅ IPasswordEncoder正确定义为抽象接口")


class TestBCryptPasswordEncoder:
    """BCryptPasswordEncoder实现测试"""

    @pytest.fixture
    def encoder(self):
        """创建BCryptPasswordEncoder实例"""
        return BCryptPasswordEncoder()

    def test_implementation_interface(self, encoder):
        """测试BCryptPasswordEncoder实现了IPasswordEncoder接口"""
        assert isinstance(encoder, IPasswordEncoder)
        print("✅ BCryptPasswordEncoder实现了IPasswordEncoder接口")

    def test_encode_generates_hash(self, encoder):
        """测试encode方法生成哈希值"""
        password = "TestPassword123!"
        hashed = encoder.encode(password)

        # BCrypt哈希应该以$2b$开头
        assert hashed.startswith("$2b$")
        # 哈希长度应该是60字符
        assert len(hashed) == 60
        print(f"✅ encode生成正确的BCrypt哈希: {hashed[:20]}...")

    def test_encode_different_hashes_for_same_password(self, encoder):
        """测试同一密码生成不同的哈希值（salt随机性）"""
        password = "SamePassword"
        hash1 = encoder.encode(password)
        hash2 = encoder.encode(password)

        assert hash1 != hash2
        print("✅ 同一密码生成不同哈希（salt随机）")

    def test_verify_correct_password(self, encoder):
        """测试verify验证正确密码"""
        password = "CorrectPassword123!"
        hashed = encoder.encode(password)

        result = encoder.verify(password, hashed)
        assert result is True
        print("✅ verify正确验证匹配的密码")

    def test_verify_incorrect_password(self, encoder):
        """测试verify拒绝错误密码"""
        password = "CorrectPassword"
        wrong_password = "WrongPassword"
        hashed = encoder.encode(password)

        result = encoder.verify(wrong_password, hashed)
        assert result is False
        print("✅ verify正确拒绝不匹配的密码")

    def test_verify_case_sensitive(self, encoder):
        """测试密码验证区分大小写"""
        password = "CaseSensitive"
        hashed = encoder.encode(password)

        assert encoder.verify(password, hashed) is True
        assert encoder.verify("casesensitive", hashed) is False
        assert encoder.verify("CASESENSITIVE", hashed) is False
        print("✅ 密码验证区分大小写")

    def test_encode_empty_password(self, encoder):
        """测试编码空密码"""
        # 空密码应该也能被编码（业务层应该拒绝）
        hashed = encoder.encode("")
        assert hashed.startswith("$2b$")
        assert encoder.verify("", hashed) is True
        print("✅ 可以编码空密码（应由业务层验证）")

    def test_encode_special_characters(self, encoder):
        """测试编码包含特殊字符的密码"""
        special_passwords = [
            "密码123!@#",  # 中文字符
            "P@$$w0rd!",    # 特殊符号
            "🔐🔑secure",   # emoji
            "a" * 100,       # 长密码
        ]

        for password in special_passwords:
            hashed = encoder.encode(password)
            assert encoder.verify(password, hashed) is True

        print("✅ 正确处理特殊字符密码")

    def test_verify_with_invalid_hash_format(self, encoder):
        """测试验证无效的哈希格式"""
        password = "test123"

        # 无效的哈希格式
        invalid_hashes = [
            "not-a-bcrypt-hash",
            "$2a$10$invalid",  # 长度不对
            "",                 # 空字符串
            "$2b$12$" + "x" * 50,  # 错误的base64编码
        ]

        for invalid_hash in invalid_hashes:
            with pytest.raises(ValueError):
                encoder.verify(password, invalid_hash)

        print("✅ 正确拒绝无效的哈希格式")

    def test_bcrypt_work_factor(self, encoder):
        """测试BCrypt work factor（计算成本）"""
        import time

        password = "test123"

        # 测量加密时间
        start = time.time()
        hashed = encoder.encode(password)
        elapsed = time.time() - start

        # BCrypt应该有明显的计算成本（通常 > 50ms）
        print(f"BCrypt编码耗时: {elapsed*1000:.1f}ms")
        assert elapsed > 0.01  # 至少10ms

        # 检查work factor是否在合理范围（$2b$12$表示12轮）
        assert "$2b$12$" in hashed
        print("✅ BCrypt使用合理的work factor (12)")

    def test_timing_attack_resistance(self, encoder):
        """测试验证操作的时序一致性"""
        import time

        password = "TestPassword123"
        hashed = encoder.encode(password)

        # 测量正确密码验证时间
        times_correct = []
        for _ in range(5):
            start = time.time()
            encoder.verify(password, hashed)
            times_correct.append(time.time() - start)

        # 测量错误密码验证时间
        times_wrong = []
        for _ in range(5):
            start = time.time()
            encoder.verify("WrongPassword", hashed)
            times_wrong.append(time.time() - start)

        avg_correct = sum(times_correct) / len(times_correct)
        avg_wrong = sum(times_wrong) / len(times_wrong)

        # 时间差应该很小（bcrypt的特性）
        time_diff_ms = abs(avg_correct - avg_wrong) * 1000

        print(f"正确密码平均: {avg_correct*1000:.2f}ms")
        print(f"错误密码平均: {avg_wrong*1000:.2f}ms")
        print(f"时间差: {time_diff_ms:.2f}ms")

        # BCrypt在算法层面就有抗时序攻击特性
        assert time_diff_ms < 10  # 差异应该很小
        print("✅ BCrypt具有时序攻击抵抗性")

    def test_encode_decode_unicode(self, encoder):
        """测试Unicode密码的编码和验证"""
        unicode_passwords = [
            "مرحبا123",      # 阿拉伯语
            "こんにちは123",  # 日语
            "Привет123",    # 俄语
            "😀😁😂123",     # Emoji
        ]

        for password in unicode_passwords:
            hashed = encoder.encode(password)
            assert encoder.verify(password, hashed) is True

        print("✅ 正确处理Unicode密码")


class TestPasswordEncoderIntegration:
    """密码编码器集成测试"""

    def test_multiple_instances_independent(self):
        """测试多个编码器实例相互独立"""
        encoder1 = BCryptPasswordEncoder()
        encoder2 = BCryptPasswordEncoder()

        password = "TestPassword"
        hash1 = encoder1.encode(password)
        hash2 = encoder2.encode(password)

        # 不同实例生成不同哈希
        assert hash1 != hash2

        # 但都能验证
        assert encoder1.verify(password, hash1)
        assert encoder1.verify(password, hash2)
        assert encoder2.verify(password, hash1)
        assert encoder2.verify(password, hash2)

        print("✅ 多个编码器实例相互独立且兼容")

    def test_real_world_password_requirements(self):
        """测试真实世界的密码要求"""
        encoder = BCryptPasswordEncoder()

        # 典型的企业密码策略要求
        passwords = [
            ("Aa1!abcd", True),      # 包含大小写、数字、特殊字符，长度8+
            ("short1!", True),       # 短密码但符合复杂度
            ("verylongpasswordwithoutspecialchars123", True),  # 长密码
            ("Password123!@#", True),  # 常见格式
        ]

        for password, should_work in passwords:
            hashed = encoder.encode(password)
            assert encoder.verify(password, hashed) == should_work

        print("✅ 支持真实世界的密码要求")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])
