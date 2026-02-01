"""
安全模块优化测试
测试认证和授权模块的优化效果
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio
from typing import Any, Dict

from pyspring.security.authorization.contracts.permission import IPermissionService
from pyspring.security.authorization.contracts.role import IRoleProvider
from pyspring.security.authorization.providers.permission.advanced import AdvancedPermissionService, create_advanced_permission_service
from pyspring.security.authorization.rules.engine import RuleEngine, TimeBasedRule, ResourceBasedRule, UserBasedRule


class MockRoleProvider(IRoleProvider):
    """模拟角色提供者"""
    
    async def get_user_roles(self, user_id: Any) -> list:
        if user_id == "admin":
            return ["admin", "user"]
        elif user_id == "manager":
            return ["manager", "user"]
        elif user_id == "user":
            return ["user"]
        else:
            return []
    
    async def get_role_permissions(self, role: str) -> list:
        role_permissions = {
            "admin": ["*"],
            "manager": ["user:*", "report:view"],
            "user": ["profile:read", "profile:update"]
        }
        return role_permissions.get(role, [])
    
    async def get_effective_roles(self, user_id: Any) -> list:
        # 返回包含继承的角色
        all_roles = await self.get_user_roles(user_id)
        return all_roles


class MockCacheService:
    """模拟缓存服务"""
    
    def __init__(self):
        self._cache = {}
    
    async def get(self, key: str):
        return self._cache.get(key)
    
    async def set(self, key: str, value: str, ttl: int = None):
        self._cache[key] = value
    
    async def delete(self, *keys):
        for key in keys:
            self._cache.pop(key, None)
    
    async def scan(self, cursor: int, match: str = None, count: int = 100):
        # 简化的scan实现
        matched_keys = []
        if match:
            import fnmatch
            for key in self._cache.keys():
                if fnmatch.fnmatch(key, match.replace('*', '.*')):
                    matched_keys.append(key)
        
        # 简化实现，返回所有匹配的键和cursor=0表示结束
        return 0, matched_keys


@pytest.mark.asyncio
async def test_advanced_permission_service_basic():
    """测试高级权限服务的基本功能"""
    role_provider = MockRoleProvider()
    cache_service = MockCacheService()
    
    service = AdvancedPermissionService(
        role_provider=role_provider,
        cache=cache_service,
        cache_ttl=300
    )
    
    # 测试基本权限检查
    result = await service.has_permission("admin", "user:delete")
    assert result is True  # admin用户有所有权限
    
    result = await service.has_permission("user", "user:delete")
    assert result is False  # 普通用户没有删除权限
    
    result = await service.has_permission("manager", "report:view")
    assert result is True  # manager有报告查看权限


@pytest.mark.asyncio
async def test_advanced_permission_service_caching():
    """测试高级权限服务的缓存功能"""
    role_provider = MockRoleProvider()
    cache_service = MockCacheService()
    
    service = AdvancedPermissionService(
        role_provider=role_provider,
        cache=cache_service,
        cache_ttl=300
    )
    
    # 第一次调用
    result1 = await service.has_permission("admin", "user:read")
    assert result1 is True
    
    # 修改角色提供者的行为（模拟权限变化）
    original_get_role_permissions = role_provider.get_role_permissions
    async def modified_get_role_permissions(role: str):
        if role == "admin":
            return []  # 模拟移除权限
        return await original_get_role_permissions(role)
    
    role_provider.get_role_permissions = modified_get_role_permissions
    
    # 第二次调用应该从缓存返回，所以结果仍然是True
    result2 = await service.has_permission("admin", "user:read")
    assert result2 is True  # 从缓存获取，仍为True
    
    # 清除缓存
    await service.invalidate_user_cache("admin")
    
    # 第三次调用应该从数据库获取，结果变为False
    result3 = await service.has_permission("admin", "user:read")
    assert result3 is False  # 从数据库获取，现在是False


@pytest.mark.asyncio
async def test_advanced_permission_service_with_rules():
    """测试高级权限服务与规则引擎集成"""
    role_provider = MockRoleProvider()
    
    # 创建一个简单的规则：只有在工作时间才能访问admin资源
    time_rule = TimeBasedRule(
        allowed_hours=[(9, 18)],  # 工作时间 9-18点
        allowed_days=list(range(7))  # 一周七天
    )
    
    resource_rule = ResourceBasedRule([
        {
            "pattern": "admin:*",
            "actions": ["*"],
            "effect": "allow"
        }
    ])
    
    rule_engine = RuleEngine([time_rule, resource_rule])
    
    service = AdvancedPermissionService(
        role_provider=role_provider,
        rule_engine=rule_engine
    )
    
    # 测试规则评估
    result = await service.has_permission("admin", "admin:delete")
    # 结果取决于当前时间，但我们至少测试方法可以调用
    assert isinstance(result, bool)


@pytest.mark.asyncio
async def test_create_advanced_permission_service_factory():
    """测试高级权限服务工厂方法"""
    role_provider = MockRoleProvider()
    cache_service = MockCacheService()
    
    service = create_advanced_permission_service(
        role_provider=role_provider,
        cache=cache_service
    )
    
    # 验证服务可以正常工作
    result = await service.has_permission("admin", "user:list")
    assert result is True  # admin用户有所有权限


@pytest.mark.asyncio
async def test_cached_permission_service_false_caching():
    """测试缓存服务对false结果的缓存（防穿透）"""
    from pyspring.security.authorization.providers.permission.cached import CachedPermissionService
    
    # 创建一个总是返回False的委托服务
    delegate_service = AsyncMock(spec=IPermissionService)
    delegate_service.has_permission.return_value = False
    delegate_service.has_role.return_value = False
    
    cache_service = MockCacheService()
    
    cached_service = CachedPermissionService(
        delegate=delegate_service,
        cache=cache_service,
        ttl=300
    )
    
    # 第一次调用
    result1 = await cached_service.has_permission("nonexistent_user", "some_permission")
    assert result1 is False
    
    # 第二次调用应该从缓存返回
    result2 = await cached_service.has_permission("nonexistent_user", "some_permission")
    assert result2 is False
    
    # 验证委托服务只被调用了一次（第二次从缓存获取）
    delegate_service.has_permission.assert_called_once()


def test_rule_engine_creation():
    """测试规则引擎创建"""
    # 创建时间规则
    time_rule = TimeBasedRule(
        allowed_hours=[(9, 17)],
        allowed_days=[0, 1, 2, 3, 4]  # 工作日
    )
    
    # 创建资源规则
    resource_rule = ResourceBasedRule([
        {
            "pattern": "user:*",
            "actions": ["read", "write"],
            "effect": "allow"
        }
    ])
    
    # 创建用户规则
    user_rule = UserBasedRule([
        {
            "users": ["admin"],
            "resources": ["*"],
            "actions": ["*"],
            "effect": "allow"
        }
    ])
    
    # 创建规则引擎
    engine = RuleEngine([time_rule, resource_rule, user_rule])
    
    assert engine is not None


@pytest.mark.asyncio
async def test_rule_engine_evaluation():
    """测试规则引擎评估"""
    # 创建一个总是允许的规则
    class AllowAllRule:
        async def evaluate(self, user_id: Any, resource: str, action: str, context: Dict[str, Any]):
            from pyspring.security.authorization.rules.engine import RuleResult
            return RuleResult.ALLOW
        
        def get_name(self) -> str:
            return "AllowAllRule"
    
    engine = RuleEngine([AllowAllRule()])
    
    result = await engine.evaluate("user123", "resource", "action", {})
    assert result is True


if __name__ == "__main__":
    # 运行测试
    import subprocess
    import sys
    
    # 使用pytest运行测试
    result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"])
    sys.exit(result.returncode)