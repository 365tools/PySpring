"""
TokenService单元测试

测试Token编码/解码、黑名单管理、职责分离
"""
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyspring.security.authentication.token.service import TokenService


class TestTokenService:
    """TokenService单元测试"""

    @pytest.fixture
    def mock_token_generator(self):
        """Mock ITokenGenerator"""
        mock = MagicMock()
        # encode方法返回字符串
        mock.encode.return_value = "mocked.jwt.token"
        # decode方法返回字典
        mock.decode.return_value = {
            "sub": "user123",
            "type": "access",
            "jti": "token-id-123",
            "exp": 1234567890
        }
        mock.get_access_token_expire.return_value = 3600
        mock.get_refresh_token_expire.return_value = 86400
        mock.get_token_type.return_value = "JWT"
        return mock

    @pytest.fixture
    def mock_db_manager(self):
        """Mock DBManagerService"""
        mock = AsyncMock()
        session_mock = AsyncMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock()
        mock.session.return_value = session_mock
        return mock

    @pytest.fixture
    def mock_cache_manager(self):
        """Mock CacheManagerService"""
        mock = AsyncMock()
        mock.get.return_value = None
        mock.set.return_value = None
        return mock

    @pytest.fixture
    def mock_entity_config(self):
        """Mock SecurityEntityConfiguration"""
        mock = MagicMock()
        mock.refresh_token_orm_model = MagicMock()
        mock.token_blacklist_orm_model = MagicMock()
        return mock

    @pytest.fixture
    def token_service(self, mock_token_generator, mock_db_manager,
                      mock_cache_manager, mock_entity_config):
        """创建TokenService实例"""
        service = TokenService()
        # 通过属性注入Mock对象（避免懒加载）
        service._token_generator = mock_token_generator
        service._db = mock_db_manager
        service._cache = mock_cache_manager
        return service

    def test_create_access_token_uses_encode(self, token_service, mock_token_generator):
        """测试create_access_token使用encode方法"""
        # Arrange
        data = {"sub": "user123", "role": "admin"}
        expires_delta = timedelta(hours=1)

        # Act
        result = token_service.create_access_token(data, expires_delta)

        # Assert
        assert result == "mocked.jwt.token"
        mock_token_generator.encode.assert_called_once()

        # 验证传递的payload包含type标记
        call_args = mock_token_generator.encode.call_args
        payload = call_args[0][0]
        assert payload["type"] == "access"
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"

    @pytest.mark.asyncio
    async def test_create_refresh_token_uses_encode_and_stores(
            self, token_service, mock_token_generator, mock_db_manager
    ):
        """测试create_refresh_token使用encode并持久化"""
        # Arrange
        data = {"sub": "user123"}
        expires_delta = timedelta(days=7)
        mock_token_generator.decode.return_value = {
            "sub": "user123",
            "type": "refresh",
            "jti": "refresh-token-id",
            "exp": 1234567890
        }

        # Act
        result = await token_service.create_refresh_token(data, expires_delta)

        # Assert
        assert result == "mocked.jwt.token"
        # 验证encode被调用
        mock_token_generator.encode.assert_called()
        # 验证decode被调用（获取exp）
        mock_token_generator.decode.assert_called_with("mocked.jwt.token")
        # 验证数据库session被使用
        mock_db_manager.session.assert_called()

    @pytest.mark.asyncio
    async def test_verify_token_uses_decode(self, token_service, mock_token_generator, mock_cache_manager):
        """测试verify_token使用decode方法"""
        # Arrange
        token = "test.jwt.token"
        # Mock decode返回完整的payload（包含jti）
        mock_token_generator.decode.return_value = {
            "sub": "user123",
            "jti": "test-jti-123",
            "exp": 9999999999
        }
        # Mock黑名单检查（Token不在黑名单中）
        mock_cache_manager.exists.return_value = False

        # Act
        result = await token_service.verify_token(token)

        # Assert
        assert result is not None
        assert result["sub"] == "user123"
        mock_token_generator.decode.assert_called_once_with(token)

    @pytest.mark.asyncio
    async def test_verify_token_checks_blacklist(
            self, token_service, mock_token_generator, mock_cache_manager
    ):
        """测试verify_token检查黑名单"""
        # Arrange
        token = "test.jwt.token"
        # 模拟Token在黑名单中
        mock_token_generator.decode.return_value = {
            "sub": "user123",
            "jti": "token-jti-123",
            "exp": 9999999999
        }
        mock_cache_manager.exists.return_value = True  # Token在黑名单中

        # Act
        result = await token_service.verify_token(token)

        # Assert
        assert result is None  # 黑名单Token返回None
        # 验证黑名单检查被调用
        mock_cache_manager.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_token_uses_decode(self, token_service, mock_token_generator):
        """测试revoke_token使用decode方法"""
        # Arrange
        token = "test.jwt.token"
        reason = "User logout"

        # Act
        result = await token_service.revoke_token(token, reason)

        # Assert
        assert result is True
        mock_token_generator.decode.assert_called_once_with(token)

    @pytest.mark.asyncio
    async def test_revoke_token_adds_to_blacklist(
            self, token_service, mock_token_generator, mock_cache_manager, mock_db_manager
    ):
        """测试revoke_token将Token加入黑名单"""
        # Arrange
        token = "test.jwt.token"
        reason = "User logout"

        # Act
        await token_service.revoke_token(token, reason)

        # Assert
        # 验证缓存写入
        mock_cache_manager.set.assert_called()
        # 验证数据库操作
        mock_db_manager.session.assert_called()

    def test_token_service_does_not_call_old_methods(self, token_service, mock_token_generator):
        """测试TokenService不调用旧的generate_access_token方法"""
        # Arrange
        data = {"sub": "user123"}

        # 确保旧方法不存在或不被调用
        if hasattr(mock_token_generator, 'generate_access_token'):
            mock_token_generator.generate_access_token = MagicMock()

        # Act
        token_service.create_access_token(data, timedelta(hours=1))

        # Assert
        mock_token_generator.encode.assert_called()
        if hasattr(mock_token_generator, 'generate_access_token'):
            mock_token_generator.generate_access_token.assert_not_called()
