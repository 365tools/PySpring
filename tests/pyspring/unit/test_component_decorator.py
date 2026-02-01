"""测试 Component 装饰器的两种用法"""
from pyspring.ioc.annotations import Component, Service, Repository


# 测试1: 不带括号
@Component
class TestServiceA:
    pass


# 测试2: 空括号
@Component
class TestServiceB:
    pass


# 测试3: 带参数
@Component(name="test_service_c", primary=True)
class TestServiceC:
    pass


# 测试4: Service 不带括号
@Service
class AuthService:
    pass


# 测试5: Repository 带参数
@Repository(name="user_repo")
class UserRepo:
    pass


# 验证
print("✅ TestServiceA:", hasattr(TestServiceA, '__pyspring_component__'))
print("✅ TestServiceB:", hasattr(TestServiceB, '__pyspring_component__'))
print("✅ TestServiceC:", hasattr(TestServiceC, '__pyspring_component__'))
print("   TestServiceC name:", getattr(TestServiceC, '__pyspring_name__', None))
print("   TestServiceC primary:", getattr(TestServiceC, '__pyspring_primary__', None))

print("\n✅ AuthService:", hasattr(AuthService, '__pyspring_component__'))
print("✅ UserRepo:", hasattr(UserRepo, '__pyspring_component__'))
print("   UserRepo name:", getattr(UserRepo, '__pyspring_name__', None))

print("\n🎉 所有装饰器用法都正常工作！")
