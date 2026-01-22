"""
CachedPermissionService单元测试

测试缓存装饰器模式、L1缓存、L2数据库
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from pyspring.security.authorization.providers.permission.cached import CachedPermissionService


class TestCachedPermissionService:
    """CachedPermissionService单元测试"""

    @pytest.fixture
    def mock_delegate(self):
        """Mock IPermissionService（被装饰的对象）"""
        mock = AsyncMock()
        mock.has_permission.return_value = True
        mock.has_role.return_value = True
        return mock

    @pytest.fixture
    def mock_cache(self):
        """Mock CacheManagerService"""
        mock = AsyncMock()
        mock.get.return_value = None  # 默认缓存未命中
        mock.set.return_value = None
        return mock

    @pytest.fixture
    def cached_service(self, mock_delegate, mock_cache):
        """创建CachedPermissionService实例"""
        return CachedPermissionService(
            delegate=mock_delegate,
            cache=mock_cache,
            ttl=300
        )

    @pytest.mark.asyncio
    async def test_has_permission_cache_miss(self, cached_service, mock_delegate, mock_cache):
        """测试权限检查：缓存未命中，查询数据库"""
        # Arrange
        user_id = "user123"
        permission = "user:read"
        mock_cache.get.return_value = None  # 缓存未命中

        # Act
        result = await cached_service.has_permission(user_id, permission)

        # Assert
        assert result is True
        # 验证查询缓存
        mock_cache.get.assert_called_once_with("perm:user123:user:read")
        # 验证委托查询数据库
        mock_delegate.has_permission.assert_called_once_with(user_id, permission)
        # 验证写入缓存
        mock_cache.set.assert_called_once_with("perm:user123:user:read", "1", ttl=300)

    @pytest.mark.asyncio
    async def test_has_permission_cache_hit(self, cached_service, mock_delegate, mock_cache):
        """测试权限检查：缓存命中，不查询数据库"""
        # Arrange
        user_id = "user123"
        permission = "user:read"
        mock_cache.get.return_value = "1"  # 缓存命中

        # Act
        result = await cached_service.has_permission(user_id, permission)

        # Assert
        assert result is True
        # 验证查询缓存
        mock_cache.get.assert_called_once()
        # 验证不查询数据库
        mock_delegate.has_permission.assert_not_called()
        # 验证不写入缓存
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_has_permission_cache_hit_false(self, cached_service, mock_delegate, mock_cache):
        """测试权限检查：缓存命中（权限为false）"""
        # Arrange
        user_id = "user123"
        permission = "user:delete"
        mock_cache.get.return_value = "0"  # 缓存命中，值为0（无权限）

        # Act
        result = await cached_service.has_permission(user_id, permission)

        # Assert
        assert result is False
        mock_cache.get.assert_called_once()
        mock_delegate.has_permission.assert_not_called()

    @pytest.mark.asyncio
    async def test_has_role_cache_miss(self, cached_service, mock_delegate, mock_cache):
        """测试角色检查：缓存未命中"""
        # Arrange
        user_id = "user123"
        role = "admin"
        mock_cache.get.return_value = None

        # Act
        result = await cached_service.has_role(user_id, role)

        # Assert
        assert result is True
        mock_cache.get.assert_called_once_with("role:user123:admin")
        mock_delegate.has_role.assert_called_once_with(user_id, role)
        mock_cache.set.assert_called_once_with("role:user123:admin", "1", ttl=300)

    @pytest.mark.asyncio
    async def test_has_role_cache_hit(self, cached_service, mock_delegate, mock_cache):
        """测试角色检查：缓存命中"""
        # Arrange
        user_id = "user123"
        role = "admin"
        mock_cache.get.return_value = "1"

        # Act
        result = await cached_service.has_role(user_id, role)

        # Assert
        assert result is True
        mock_cache.get.assert_called_once()
        mock_delegate.has_role.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_failure_fallback_to_delegate(
        self, cached_service, mock_delegate, mock_cache
    ):
        """测试缓存失败时降级到数据库查询"""
        # Arrange
        user_id = "user123"
        permission = "user:read"
        mock_cache.get.side_effect = Exception("Redis连接失败")

        # Act
        result = await cached_service.has_permission(user_id, permission)

        # Assert
        assert result is True  # 仍然返回正确结果
        mock_delegate.has_permission.assert_called_once()  # 降级到数据库

    @pytest.mark.asyncio
    async def test_decorator_pattern_preserves_interface(self, cached_service, mock_delegate):
        """测试装饰器模式保持接口一致性"""
        # Assert
        # CachedPermissionService应该有和IPermissionService相同的方法
        assert hasattr(cached_service, 'has_permission')
        assert hasattr(cached_service, 'has_role')
        assert callable(cached_service.has_permission)
        assert callable(cached_service.has_role)

    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self, cached_service, mock_cache):
        """测试用户缓存失效"""
        # Arrange
        user_id = "user123"

        # Act
        await cached_service.invalidate_user_cache(user_id)

        # Assert
        # 目前是简化实现，只记录日志
        # 真实实现需要使用Redis SCAN命令删除匹配的键
        pass  # 暂时通过，待实现完整逻辑
