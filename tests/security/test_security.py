"""
pyspring-security：安全模块测试

验证独立 security starter 的核心能力：
- JWT / 认证配置模型
- BCrypt 密码编码器（哈希/校验）
- 认证/授权接口契约
"""
import pytest

from pyspring.security.authentication.contracts.config import JWTConfig, AuthenticationConfig
from pyspring.security.authentication.contracts.password import IPasswordEncoder
from pyspring.security.authentication.providers.password.bcrypt import BCryptPasswordEncoder
from pyspring.security.authentication.contracts.token import ITokenService
from pyspring.security.authentication.contracts.login import ILoginProvider


class TestJWTConfig:
    """JWT 配置"""

    def test_defaults(self):
        cfg = JWTConfig()
        assert cfg.algorithm == "HS256"
        assert cfg.access_token_expire == 3600
        assert cfg.refresh_token_expire == 2592000

    def test_secret_key_default(self):
        cfg = JWTConfig()
        assert cfg.secret_key  # 默认提供非空 secret_key


class TestAuthenticationConfig:
    """认证配置"""

    def test_contains_jwt(self):
        cfg = AuthenticationConfig()
        assert isinstance(cfg.jwt, JWTConfig)
        assert cfg.jwt.algorithm == "HS256"


class TestBCryptPasswordEncoder:
    """BCrypt 密码编码器"""

    def setup_method(self):
        self.encoder = BCryptPasswordEncoder()

    def test_encode_produces_hash(self):
        hashed = self.encoder.encode("secret123")
        assert hashed != "secret123"
        assert len(hashed) > 20

    def test_verify_correct(self):
        hashed = self.encoder.encode("secret123")
        assert self.encoder.verify("secret123", hashed) is True

    def test_verify_wrong(self):
        hashed = self.encoder.encode("secret123")
        assert self.encoder.verify("wrong", hashed) is False

    def test_is_password_encoder(self):
        assert isinstance(self.encoder, IPasswordEncoder)


class TestAuthContracts:
    """认证接口契约"""

    def test_itoken_service_importable(self):
        assert ITokenService is not None

    def test_ilogin_provider_importable(self):
        assert ILoginProvider is not None
