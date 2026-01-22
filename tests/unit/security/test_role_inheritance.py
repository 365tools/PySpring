"""
角色继承功能单元测试

测试IRoleProvider的角色继承、有效角色计算
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from pyspring.security.authorization.providers.role.database import DefaultRoleProvider


class TestRoleInheritance:
    """角色继承功能测试"""

    @pytest.fixture
    def mock_db_manager(self):
        """Mock DBManagerService"""
        mock = AsyncMock()
        session_mock = AsyncMock()
        session_mock.__aenter__ = AsyncMock(return_value=session_mock)
        session_mock.__aexit__ = AsyncMock()
        session_mock.execute = AsyncMock()
        mock.session.return_value = session_mock
        return mock

    @pytest.fixture
    def mock_entity_config(self):
        """Mock SecurityEntityConfiguration"""
        mock = MagicMock()
        mock.role_orm_model = MagicMock()
        mock.user_orm_model = MagicMock()
        mock.user_role_orm_model = MagicMock()
        mock.permission_orm_model = MagicMock()
        mock.role_permission_orm_model = MagicMock()
        return mock

    @pytest.fixture
    def role_provider(self, mock_db_manager, mock_entity_config):
        """创建DefaultRoleProvider实例"""
        return DefaultRoleProvider(
            db_manager=mock_db_manager,
            component=mock_entity_config
        )

    @pytest.mark.asyncio
    async def test_get_role_hierarchy(self, role_provider):
        """测试获取角色继承层次"""
        # Act
        hierarchy = await role_provider.get_role_hierarchy()

        # Assert
        assert 'admin' in hierarchy
        assert 'manager' in hierarchy
        assert 'manager' in hierarchy['admin']
        assert 'user' in hierarchy['admin']
        assert 'user' in hierarchy['manager']

    @pytest.mark.asyncio
    async def test_get_effective_roles_with_admin(self, role_provider, mock_db_manager):
        """测试admin用户的有效角色（包含继承）"""
        # Arrange
        user_id = "user123"
        # Mock数据库返回admin角色
        result_mock = MagicMock()
        result_mock.scalars().all.return_value = ['admin']
        session_mock = await mock_db_manager.session()
        session_mock.__aenter__.return_value.execute.return_value = result_mock

        # Act
        effective_roles = await role_provider.get_effective_roles(user_id)

        # Assert
        assert 'admin' in effective_roles
        assert 'manager' in effective_roles
        assert 'user' in effective_roles
        assert len(effective_roles) == 3

    @pytest.mark.asyncio
    async def test_get_effective_roles_with_manager(self, role_provider, mock_db_manager):
        """测试manager用户的有效角色"""
        # Arrange
        user_id = "user456"
        result_mock = MagicMock()
        result_mock.scalars().all.return_value = ['manager']
        session_mock = await mock_db_manager.session()
        session_mock.__aenter__.return_value.execute.return_value = result_mock

        # Act
        effective_roles = await role_provider.get_effective_roles(user_id)

        # Assert
        assert 'manager' in effective_roles
        assert 'user' in effective_roles
        assert 'admin' not in effective_roles
        assert len(effective_roles) == 2

    @pytest.mark.asyncio
    async def test_get_effective_roles_with_user(self, role_provider, mock_db_manager):
        """测试普通用户的有效角色（无继承）"""
        # Arrange
        user_id = "user789"
        result_mock = MagicMock()
        result_mock.scalars().all.return_value = ['user']
        session_mock = await mock_db_manager.session()
        session_mock.__aenter__.return_value.execute.return_value = result_mock

        # Act
        effective_roles = await role_provider.get_effective_roles(user_id)

        # Assert
        assert effective_roles == ['user']
        assert len(effective_roles) == 1

    @pytest.mark.asyncio
    async def test_role_hierarchy_prevents_duplication(self, role_provider, mock_db_manager):
        """测试角色继承不会导致重复"""
        # Arrange
        user_id = "user_multi"
        # 用户同时拥有admin和manager角色
        result_mock = MagicMock()
        result_mock.scalars().all.return_value = ['admin', 'manager']
        session_mock = await mock_db_manager.session()
        session_mock.__aenter__.return_value.execute.return_value = result_mock

        # Act
        effective_roles = await role_provider.get_effective_roles(user_id)

        # Assert
        # 即使admin和manager都继承user，user只应出现一次
        assert effective_roles.count('user') == 1
        assert effective_roles.count('admin') == 1
        assert effective_roles.count('manager') == 1
        assert len(effective_roles) == 3


class TestPermissionServiceWithInheritance:
    """测试PermissionService使用角色继承"""

    @pytest.mark.asyncio
    async def test_has_role_checks_inherited_roles(self):
        """测试has_role检查继承的角色"""
        # Arrange
        from pyspring.security.authorization.providers.permission.default import DefaultPermissionService
        
        mock_role_provider = AsyncMock()
        # 用户只有admin角色，但通过继承拥有manager和user
        mock_role_provider.get_effective_roles.return_value = ['admin', 'manager', 'user']
        
        permission_service = DefaultPermissionService(role_provider=mock_role_provider)

        # Act & Assert
        assert await permission_service.has_role("user123", "admin") is True
        assert await permission_service.has_role("user123", "manager") is True
        assert await permission_service.has_role("user123", "user") is True
        assert await permission_service.has_role("user123", "guest") is False

    @pytest.mark.asyncio
    async def test_has_permission_uses_inherited_roles(self):
        """测试has_permission使用继承的角色权限"""
        # Arrange
        from pyspring.security.authorization.providers.permission.default import DefaultPermissionService
        
        mock_role_provider = AsyncMock()
        # admin继承manager和user的角色
        mock_role_provider.get_effective_roles.return_value = ['admin', 'manager', 'user']
        # admin权限
        mock_role_provider.get_role_permissions.side_effect = lambda role: {
            'admin': ['admin:*'],
            'manager': ['user:write', 'article:write'],
            'user': ['user:read', 'article:read']
        }.get(role, [])
        
        permission_service = DefaultPermissionService(role_provider=mock_role_provider)

        # Act & Assert
        # admin拥有admin:*权限
        assert await permission_service.has_permission("user123", "admin:delete") is True
        # 通过继承manager拥有article:write权限
        assert await permission_service.has_permission("user123", "article:write") is True
        # 通过继承user拥有article:read权限
        assert await permission_service.has_permission("user123", "article:read") is True
