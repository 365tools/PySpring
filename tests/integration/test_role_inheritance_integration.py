"""
角色继承功能集成测试

测试场景：
1. 真实角色继承计算（admin → manager → user）
2. 权限累加验证
3. 缓存集成验证
4. 实际业务场景测试
"""
import io
import sys

# 设置标准输出编码为UTF-8，解决Windows下中文乱码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import os
from typing import Set, List
from unittest.mock import Mock, AsyncMock

os.environ['JWT_SECRET_KEY'] = 'test-secret-key-for-role-inheritance-integration-testing'


class TestRoleInheritanceIntegration:
    """角色继承集成测试"""

    def test_1_basic_role_inheritance(self):
        """测试1: 基础角色继承功能"""
        from pyspring.security.authorization.providers.role import RoleInheritanceResolver, InMemoryRoleProvider
        
        async def run_test():
            print("\n【测试1: 基础角色继承】\n")
            
            # 创建角色提供者
            role_provider = InMemoryRoleProvider()
            
            # 配置角色继承关系
            # admin继承manager权限，manager继承user权限
            role_config = {
                "admin": {
                    "inherits": ["manager"],
                    "permissions": ["system:admin", "user:delete", "config:write"]
                },
                "manager": {
                    "inherits": ["user"],
                    "permissions": ["team:manage", "report:view", "user:edit"]
                },
                "user": {
                    "inherits": [],
                    "permissions": ["profile:view", "profile:edit", "content:read"]
                }
            }
            
            # 初始化角色数据
            for role_name, config in role_config.items():
                await role_provider.add_role(role_name, config["permissions"], config["inherits"])
            
            # 创建继承解析器
            resolver = RoleInheritanceResolver(role_provider)
            
            # 测试admin角色的有效权限
            print("测试admin角色继承：")
            admin_permissions = await resolver.resolve_permissions(["admin"])
            expected_admin_perms = {
                # admin自有权限
                "system:admin", "user:delete", "config:write",
                # 继承自manager
                "team:manage", "report:view", "user:edit",
                # 继承自user（通过manager）
                "profile:view", "profile:edit", "content:read"
            }
            
            assert admin_permissions == expected_admin_perms, f"权限不匹配: {admin_permissions} != {expected_admin_perms}"
            print(f"✅ admin拥有 {len(admin_permissions)} 个权限（包括继承）")
            for perm in sorted(admin_permissions):
                print(f"   - {perm}")
            
            # 测试manager角色的有效权限
            print("\n测试manager角色继承：")
            manager_permissions = await resolver.resolve_permissions(["manager"])
            expected_manager_perms = {
                # manager自有权限
                "team:manage", "report:view", "user:edit",
                # 继承自user
                "profile:view", "profile:edit", "content:read"
            }
            
            assert manager_permissions == expected_manager_perms, f"权限不匹配"
            print(f"✅ manager拥有 {len(manager_permissions)} 个权限（包括继承）")
            for perm in sorted(manager_permissions):
                print(f"   - {perm}")
            
            # 测试user角色（无继承）
            print("\n测试user角色（无继承）：")
            user_permissions = await resolver.resolve_permissions(["user"])
            expected_user_perms = {"profile:view", "profile:edit", "content:read"}
            
            assert user_permissions == expected_user_perms
            print(f"✅ user拥有 {len(user_permissions)} 个权限")
            for perm in sorted(user_permissions):
                print(f"   - {perm}")
            
            return True
        
        result = asyncio.run(run_test())
        assert result

    def test_2_multiple_roles_combination(self):
        """测试2: 多角色组合（用户同时拥有多个角色）"""
        from pyspring.security.authorization.providers.role import RoleInheritanceResolver, InMemoryRoleProvider
        
        async def run_test():
            print("\n【测试2: 多角色组合】\n")
            
            role_provider = InMemoryRoleProvider()
            
            # 配置特殊角色场景
            roles = {
                "developer": {
                    "inherits": ["user"],
                    "permissions": ["code:read", "code:write", "deploy:staging"]
                },
                "tester": {
                    "inherits": ["user"],
                    "permissions": ["test:run", "bug:create", "test:report"]
                },
                "user": {
                    "inherits": [],
                    "permissions": ["profile:view", "profile:edit"]
                }
            }
            
            for name, config in roles.items():
                await role_provider.add_role(name, config["permissions"], config["inherits"])
            
            resolver = RoleInheritanceResolver(role_provider)
            
            # 测试同时拥有developer和tester角色
            print("测试用户同时拥有developer和tester角色：")
            combined_permissions = await resolver.resolve_permissions(["developer", "tester"])
            
            expected_combined = {
                # developer权限
                "code:read", "code:write", "deploy:staging",
                # tester权限
                "test:run", "bug:create", "test:report",
                # user权限（两个角色都继承）
                "profile:view", "profile:edit"
            }
            
            assert combined_permissions == expected_combined
            print(f"✅ 组合后拥有 {len(combined_permissions)} 个唯一权限")
            for perm in sorted(combined_permissions):
                print(f"   - {perm}")
            
            # 验证去重逻辑
            user_perm_count = sum(1 for p in combined_permissions if p.startswith("profile:"))
            assert user_perm_count == 2, "user权限应该被去重"
            print(f"✅ user权限被正确去重（只出现一次）")
            
            return True
        
        result = asyncio.run(run_test())
        assert result

    def test_3_circular_inheritance_detection(self):
        """测试3: 循环继承检测"""
        from pyspring.security.authorization.providers.role import RoleInheritanceResolver, InMemoryRoleProvider
        
        async def run_test():
            print("\n【测试3: 循环继承检测】\n")
            
            role_provider = InMemoryRoleProvider()
            
            # 尝试创建循环继承：role_a → role_b → role_c → role_a
            await role_provider.add_role("role_a", ["perm_a"], ["role_b"])
            await role_provider.add_role("role_b", ["perm_b"], ["role_c"])
            await role_provider.add_role("role_c", ["perm_c"], ["role_a"])  # 循环
            
            resolver = RoleInheritanceResolver(role_provider)
            
            print("尝试解析循环继承的角色：")
            try:
                # 解析器应该检测到循环并处理
                permissions = await resolver.resolve_permissions(["role_a"])
                
                # 验证所有权限都被收集（即使有循环）
                expected_perms = {"perm_a", "perm_b", "perm_c"}
                assert permissions == expected_perms
                
                print(f"✅ 循环继承被正确处理")
                print(f"✅ 收集到所有权限: {sorted(permissions)}")
                return True
            except RecursionError:
                print("❌ 出现递归错误，循环检测失败")
                return False
        
        result = asyncio.run(run_test())
        assert result

    def test_4_role_inheritance_with_cache(self):
        """测试4: 角色继承与缓存集成"""
        from pyspring.security.authorization.providers.role import RoleInheritanceResolver, InMemoryRoleProvider
        from pyspring.security.authorization.providers.permission import CachedPermissionService, DefaultPermissionService
        
        async def run_test():
            print("\n【测试4: 角色继承与缓存集成】\n")
            
            # Mock缓存
            mock_cache = AsyncMock()
            mock_cache.get = AsyncMock(return_value=None)  # 初始缓存未命中
            mock_cache.set = AsyncMock()
            
            # 配置角色
            role_provider = InMemoryRoleProvider()
            await role_provider.add_role("admin", ["admin:all"], ["manager"])
            await role_provider.add_role("manager", ["team:manage"], ["user"])
            await role_provider.add_role("user", ["profile:view"], [])
            
            resolver = RoleInheritanceResolver(role_provider)
            
            # 创建权限服务
            base_service = DefaultPermissionService(role_provider, resolver)
            cached_service = CachedPermissionService(base_service, mock_cache)
            
            # 第一次检查（缓存未命中）
            print("第一次权限检查（缓存未命中）：")
            result1 = await cached_service.has_permission("user_123", ["admin"], "admin:all")
            assert result1 is True
            print("✅ 权限检查通过")
            
            # 验证缓存被设置
            assert mock_cache.set.called
            print(f"✅ 缓存已设置，调用次数: {mock_cache.set.call_count}")
            
            # 模拟缓存命中
            mock_cache.get = AsyncMock(return_value={"admin:all", "team:manage", "profile:view"})
            
            # 第二次检查（缓存命中）
            print("\n第二次权限检查（缓存命中）：")
            result2 = await cached_service.has_permission("user_123", ["admin"], "team:manage")
            assert result2 is True
            print("✅ 从缓存读取权限成功")
            
            return True
        
        result = asyncio.run(run_test())
        assert result

    def test_5_real_world_scenario(self):
        """测试5: 真实业务场景（企业权限管理）"""
        from pyspring.security.authorization.providers.role import RoleInheritanceResolver, InMemoryRoleProvider
        from pyspring.security.authorization.providers.permission import DefaultPermissionService
        
        async def run_test():
            print("\n【测试5: 真实业务场景】\n")
            
            role_provider = InMemoryRoleProvider()
            
            # 配置企业角色层级
            enterprise_roles = {
                "ceo": {
                    "inherits": ["cto", "cfo", "coo"],
                    "permissions": ["company:strategic_decision", "board:vote"]
                },
                "cto": {
                    "inherits": ["tech_lead"],
                    "permissions": ["tech:budget", "tech:hire"]
                },
                "cfo": {
                    "inherits": ["accountant"],
                    "permissions": ["finance:budget", "finance:approve"]
                },
                "coo": {
                    "inherits": ["manager"],
                    "permissions": ["operations:manage", "process:optimize"]
                },
                "tech_lead": {
                    "inherits": ["developer"],
                    "permissions": ["code:review", "architecture:design"]
                },
                "developer": {
                    "inherits": ["employee"],
                    "permissions": ["code:write", "deploy:dev"]
                },
                "accountant": {
                    "inherits": ["employee"],
                    "permissions": ["invoice:view", "expense:record"]
                },
                "manager": {
                    "inherits": ["employee"],
                    "permissions": ["team:manage", "report:create"]
                },
                "employee": {
                    "inherits": [],
                    "permissions": ["profile:view", "attendance:check"]
                }
            }
            
            for role, config in enterprise_roles.items():
                await role_provider.add_role(role, config["permissions"], config["inherits"])
            
            resolver = RoleInheritanceResolver(role_provider)
            permission_service = DefaultPermissionService(role_provider, resolver)
            
            # 场景1: CEO访问所有资源
            print("场景1: CEO权限验证")
            ceo_checks = [
                ("company:strategic_decision", True, "战略决策权"),
                ("tech:budget", True, "技术预算（继承自CTO）"),
                ("finance:approve", True, "财务审批（继承自CFO）"),
                ("code:write", True, "代码编写（继承自developer）"),
                ("profile:view", True, "基础权限（继承自employee）"),
            ]
            
            for perm, expected, desc in ceo_checks:
                result = await permission_service.has_permission("ceo_user", ["ceo"], perm)
                status = "✅" if result == expected else "❌"
                print(f"  {status} {desc}: {perm}")
                assert result == expected
            
            # 场景2: Developer访问权限
            print("\n场景2: Developer权限验证")
            dev_checks = [
                ("code:write", True, "代码编写权"),
                ("deploy:dev", True, "开发环境部署"),
                ("profile:view", True, "基础权限"),
                ("tech:budget", False, "无技术预算权（需要tech_lead及以上）"),
                ("company:strategic_decision", False, "无战略决策权"),
            ]
            
            for perm, expected, desc in dev_checks:
                result = await permission_service.has_permission("dev_user", ["developer"], perm)
                status = "✅" if result == expected else "❌"
                print(f"  {status} {desc}: {perm}")
                assert result == expected
            
            # 场景3: Tech Lead的特殊权限
            print("\n场景3: Tech Lead权限验证")
            ceo_perms = await resolver.resolve_permissions(["ceo"])
            tech_lead_perms = await resolver.resolve_permissions(["tech_lead"])
            
            print(f"✅ CEO拥有 {len(ceo_perms)} 个权限")
            print(f"✅ Tech Lead拥有 {len(tech_lead_perms)} 个权限")
            
            # Tech Lead应该有developer的所有权限
            developer_perms = await resolver.resolve_permissions(["developer"])
            assert developer_perms.issubset(tech_lead_perms)
            print(f"✅ Tech Lead包含所有Developer权限")
            
            return True
        
        result = asyncio.run(run_test())
        assert result


def run_all_tests():
    """运行所有集成测试"""
    print("=" * 80)
    print("角色继承功能集成测试套件")
    print("=" * 80)
    
    test_suite = TestRoleInheritanceIntegration()
    
    tests = [
        ("基础角色继承", test_suite.test_1_basic_role_inheritance),
        ("多角色组合", test_suite.test_2_multiple_roles_combination),
        ("循环继承检测", test_suite.test_3_circular_inheritance_detection),
        ("角色继承与缓存", test_suite.test_4_role_inheritance_with_cache),
        ("真实业务场景", test_suite.test_5_real_world_scenario),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n{'=' * 80}")
        print(f"测试: {name}")
        print(f"{'=' * 80}")
        try:
            test_func()
            passed += 1
            print(f"\n✅ {name} - 通过")
        except AssertionError as e:
            failed += 1
            print(f"\n❌ {name} - 失败: {e}")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} - 错误: {type(e).__name__}: {e}")
    
    print(f"\n{'=' * 80}")
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print(f"{'=' * 80}")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
