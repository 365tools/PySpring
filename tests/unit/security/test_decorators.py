"""
权限装饰器单元测试

测试@require_permission、@require_role等装饰器
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException

from pyspring.security.authorization.decorators.require import (
    require_permission,
    require_role,
    require_any_permission,
    require_all_permissions
)


class TestPermissionDecorators:
    """权限装饰器测试"""

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI Request"""
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        request.state.user_id = "user123"
        return request

    @pytest.fixture
    def mock_permission_service(self):
        """Mock IPermissionService"""
        mock = AsyncMock()
        mock.has_permission.return_value = True
        mock.has_role.return_value = True
        return mock

    @pytest.mark.asyncio
    async def test_require_permission_success(self, mock_request, mock_permission_service):
        """测试@require_permission装饰器通过"""
        # Arrange
        @require_permission("user:read")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        # Mock ApplicationContext
        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act
            result = await test_endpoint(mock_request)

            # Assert
            assert result == {"status": "ok"}
            mock_permission_service.has_permission.assert_called_once_with("user123", "user:read")

    @pytest.mark.asyncio
    async def test_require_permission_denied(self, mock_request, mock_permission_service):
        """测试@require_permission装饰器拒绝"""
        # Arrange
        mock_permission_service.has_permission.return_value = False

        @require_permission("admin:delete")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        # Mock ApplicationContext
        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await test_endpoint(mock_request)

            assert exc_info.value.status_code == 403
            assert "Permission denied" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_require_role_success(self, mock_request, mock_permission_service):
        """测试@require_role装饰器通过"""
        # Arrange
        @require_role("admin")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act
            result = await test_endpoint(mock_request)

            # Assert
            assert result == {"status": "ok"}
            mock_permission_service.has_role.assert_called_once_with("user123", "admin")

    @pytest.mark.asyncio
    async def test_require_any_permission_success(self, mock_request, mock_permission_service):
        """测试@require_any_permission装饰器（至少一个权限）"""
        # Arrange
        # 第一个权限拒绝，第二个权限通过
        mock_permission_service.has_permission.side_effect = [False, True]

        @require_any_permission("admin:*", "manager:*")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act
            result = await test_endpoint(mock_request)

            # Assert
            assert result == {"status": "ok"}
            assert mock_permission_service.has_permission.call_count == 2

    @pytest.mark.asyncio
    async def test_require_all_permissions_success(self, mock_request, mock_permission_service):
        """测试@require_all_permissions装饰器（所有权限）"""
        # Arrange
        mock_permission_service.has_permission.return_value = True

        @require_all_permissions("user:read", "user:write")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act
            result = await test_endpoint(mock_request)

            # Assert
            assert result == {"status": "ok"}
            assert mock_permission_service.has_permission.call_count == 2

    @pytest.mark.asyncio
    async def test_require_all_permissions_denied(self, mock_request, mock_permission_service):
        """测试@require_all_permissions装饰器拒绝（缺少一个权限）"""
        # Arrange
        # 第一个权限通过，第二个权限拒绝
        mock_permission_service.has_permission.side_effect = [True, False]

        @require_all_permissions("user:read", "admin:write")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await test_endpoint(mock_request)

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_permission_no_user_id(self, mock_permission_service):
        """测试装饰器：用户未认证（无user_id）"""
        # Arrange
        request_no_user = MagicMock(spec=Request)
        request_no_user.state = MagicMock()
        request_no_user.state.user_id = None

        @require_permission("user:read")
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await test_endpoint(request_no_user)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_require_multiple_permissions_require_all(
        self, mock_request, mock_permission_service
    ):
        """测试多个权限require_all=True"""
        # Arrange
        mock_permission_service.has_permission.return_value = True

        @require_permission(["user:read", "user:write"], require_all=True)
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act
            result = await test_endpoint(mock_request)

            # Assert
            assert result == {"status": "ok"}
            # 应该检查两个权限
            assert mock_permission_service.has_permission.call_count == 2

    @pytest.mark.asyncio
    async def test_require_multiple_roles_require_all_false(
        self, mock_request, mock_permission_service
    ):
        """测试多个角色require_all=False（任意一个）"""
        # Arrange
        # 第一个角色拒绝，第二个角色通过
        mock_permission_service.has_role.side_effect = [False, True]

        @require_role(["admin", "manager"], require_all=False)
        async def test_endpoint(request: Request):
            return {"status": "ok"}

        with patch('pyspring.security.authorization.decorators.require.ApplicationContext') as mock_ctx:
            mock_ctx.get_by_type.return_value = mock_permission_service

            # Act
            result = await test_endpoint(mock_request)

            # Assert
            assert result == {"status": "ok"}
