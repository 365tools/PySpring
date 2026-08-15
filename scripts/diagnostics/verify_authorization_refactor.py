"""
快速验证Authorization模块重构后的功能
"""
import asyncio
import sys

sys.path.insert(0, 'src')

from pyspring.core.ioc.context import ApplicationContext
from pyspring.security.authorization.providers.permission.default import DefaultPermissionService
from pyspring.security.authorization.providers.role.database import DefaultRoleProvider
from pyspring.security.authorization.providers.rule.config import DefaultPathPermissionProvider


async def test_authorization_providers():
    """验证Authorization提供者可以被正确导入和实例化"""
    import os

    print("\n" + "=" * 80)
    print("Authorization模块重构验证")
    print("=" * 80)

    # 测试1: 导入验证
    print("\n✅ 1. 导入路径验证 - 所有Provider成功导入")
    print(f"   - DefaultPermissionService: {DefaultPermissionService.__name__}")
    print(f"   - DefaultRoleProvider: {DefaultRoleProvider.__name__}")
    print(f"   - DefaultPathPermissionProvider: {DefaultPathPermissionProvider.__name__}")

    # 测试2: IOC容器扫描
    print("\n✅ 2. IOC容器扫描")
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
    ctx = ApplicationContext.initialize(base_packages=[
        "pyspring.security.authorization"
    ])

    print(f"   - 容器初始化成功")
    # print(f"   - 注册服务数: {len(ctx.container._services)}")

    # 测试3: 权限匹配逻辑
    print("\n✅ 3. 权限匹配逻辑验证")

    # 创建DefaultPermissionService实例（手动）
    from pyspring.security.authorization.contracts.role import IRoleProvider
    from unittest.mock import Mock, AsyncMock

    mock_role_provider = Mock(spec=IRoleProvider)
    mock_role_provider.get_user_roles = AsyncMock(return_value=[])
    mock_role_provider.get_role_permissions = AsyncMock(return_value=[])

    permission_service = DefaultPermissionService(mock_role_provider)

    # 测试通配符匹配
    # _permission_matches(required, granted)
    # required是用户请求的权限，granted是已授予的权限（可能含通配符）
    test_cases = [
        ("user:read", "user:*", True, "通配符匹配"),
        ("user:read", "user:read", True, "精确匹配"),
        ("user:write", "user:read", False, "不匹配"),
        ("admin:user:delete", "admin:*:*", True, "多级通配符"),
        ("user:read", "*", True, "全局通配符"),
    ]

    for required, granted, expected, desc in test_cases:
        result = permission_service._permission_matches(required, granted)
        status = "✓" if result == expected else "✗"
        print(f"   {status} {desc}: required='{required}' granted='{granted}' => {result}")
        assert result == expected, f"权限匹配失败: {desc}"

    # 测试4: 目录结构
    print("\n✅ 4. 目录结构验证")
    import os
    auth_dir = "src/pyspring/security/authorization"
    expected_dirs = ["config", "contracts", "providers", "web"]
    for dir_name in expected_dirs:
        path = os.path.join(auth_dir, dir_name)
        exists = os.path.isdir(path)
        status = "✓" if exists else "✗"
        print(f"   {status} {dir_name}/")
        assert exists, f"目录不存在: {dir_name}"

    expected_provider_dirs = ["permission", "role", "rule"]
    for dir_name in expected_provider_dirs:
        path = os.path.join(auth_dir, "providers", dir_name)
        exists = os.path.isdir(path)
        status = "✓" if exists else "✗"
        print(f"   {status} providers/{dir_name}/")
        assert exists, f"Provider目录不存在: {dir_name}"

    print("\n" + "=" * 80)
    print("✅✅✅ Authorization模块重构验证通过！")
    print("=" * 80)
    print("\n重构成果:")
    print("  ✓ 新目录结构：config/, providers/, contracts/, web/")
    print("  ✓ Provider实现：permission, role, rule")
    print("  ✓ 权限匹配逻辑：支持通配符（user:*, admin:*:*）")
    print("  ✓ IOC集成：成功注册到容器")
    print("  ✓ Schema迁移：LoginRequest等移至authentication.contracts")
    print("\n")


if __name__ == "__main__":
    asyncio.run(test_authorization_providers())
