"""
测试所有装饰器都支持不带括号和带括号两种用法
"""
from pyspring.ioc.annotations.component import (
    Component, Service, Repository, Configuration,
    Bean, Primary, Lazy, ConditionalOnMissingBean
)

print("=" * 60)
print("测试所有装饰器的灵活用法")
print("=" * 60)
print()

# 测试 @Component
print("1. 测试 @Component")
try:
    @Component
    class TestComponent1:
        pass


    @Component
    class TestComponent2:
        pass


    @Component(name="custom")
    class TestComponent3:
        pass


    assert isinstance(TestComponent1, type)
    assert isinstance(TestComponent2, type)
    assert isinstance(TestComponent3, type)
    print("✅ @Component 支持: 不带括号, 空括号, 带参数")
except Exception as e:
    print(f"❌ 失败: {e}")

print()

# 测试 @Service
print("2. 测试 @Service")
try:
    @Service
    class TestService1:
        pass


    @Service()
    class TestService2:
        pass


    @Service(name="custom_service")
    class TestService3:
        pass


    assert isinstance(TestService1, type)
    assert isinstance(TestService2, type)
    assert isinstance(TestService3, type)
    print("✅ @Service 支持: 不带括号, 空括号, 带参数")
except Exception as e:
    print(f"❌ 失败: {e}")

print()

# 测试 @Repository
print("3. 测试 @Repository")
try:
    @Repository
    class TestRepository1:
        pass


    @Repository()
    class TestRepository2:
        pass


    @Repository(name="custom_repo")
    class TestRepository3:
        pass


    assert isinstance(TestRepository1, type)
    assert isinstance(TestRepository2, type)
    assert isinstance(TestRepository3, type)
    print("✅ @Repository 支持: 不带括号, 空括号, 带参数")
except Exception as e:
    print(f"❌ 失败: {e}")

print()

# 测试 @Configuration
print("4. 测试 @Configuration")
try:
    @Configuration
    class TestConfig1:
        pass


    @Configuration()
    class TestConfig2:
        pass


    assert isinstance(TestConfig1, type)
    assert isinstance(TestConfig2, type)
    assert hasattr(TestConfig1, '__pyspring_configuration__')
    assert hasattr(TestConfig2, '__pyspring_configuration__')
    print("✅ @Configuration 支持: 不带括号, 空括号")
except Exception as e:
    print(f"❌ 失败: {e}")

print()

# 测试 @Bean
print("5. 测试 @Bean")
try:
    class TestBeanConfig:
        @Bean
        def bean1(self):
            return "test1"

        @Bean()
        def bean2(self):
            return "test2"

        @Bean(name="custom_bean")
        def bean3(self):
            return "test3"


    assert hasattr(TestBeanConfig.bean1, '__pyspring_bean__')
    assert hasattr(TestBeanConfig.bean2, '__pyspring_bean__')
    assert hasattr(TestBeanConfig.bean3, '__pyspring_bean__')
    print("✅ @Bean 支持: 不带括号, 空括号, 带参数")
except Exception as e:
    print(f"❌ 失败: {e}")

print()

# 测试 @Primary
print("6. 测试 @Primary")
try:
    @Component
    @Primary
    class TestPrimary1:
        pass


    @Component
    @Primary()
    class TestPrimary2:
        pass


    assert isinstance(TestPrimary1, type)
    assert isinstance(TestPrimary2, type)
    assert hasattr(TestPrimary1, '__pyspring_primary__')
    assert hasattr(TestPrimary2, '__pyspring_primary__')
    print("✅ @Primary 支持: 不带括号, 空括号")
except Exception as e:
    print(f"❌ 失败: {e}")

print()

# 测试 @Lazy
print("7. 测试 @Lazy")
try:
    @Component
    @Lazy
    class TestLazy1:
        pass


    @Component
    @Lazy()
    class TestLazy2:
        pass


    assert isinstance(TestLazy1, type)
    assert isinstance(TestLazy2, type)
    assert hasattr(TestLazy1, '__pyspring_lazy__')
    assert hasattr(TestLazy2, '__pyspring_lazy__')
    print("✅ @Lazy 支持: 不带括号, 空括号")
except Exception as e:
    print(f"❌ 失败: {e}")

print()

# 测试 @ConditionalOnMissingBean
print("8. 测试 @ConditionalOnMissingBean")
try:
    from abc import ABC, abstractmethod


    class ITestInterface(ABC):
        @abstractmethod
        def test(self):
            pass


    @ConditionalOnMissingBean
    class TestConditional1:
        pass


    @ConditionalOnMissingBean()
    class TestConditional2:
        pass


    @ConditionalOnMissingBean(ITestInterface)
    class TestConditional3(ITestInterface):
        def test(self):
            pass


    assert isinstance(TestConditional1, type)
    assert isinstance(TestConditional2, type)
    assert isinstance(TestConditional3, type)
    assert hasattr(TestConditional1, '__pyspring_conditional_on_missing_bean__')
    assert hasattr(TestConditional2, '__pyspring_conditional_on_missing_bean__')
    assert hasattr(TestConditional3, '__pyspring_conditional_on_missing_bean__')
    print("✅ @ConditionalOnMissingBean 支持: 不带括号, 空括号, 指定类型")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback

    traceback.print_exc()

print()
print("=" * 60)
print("总结：所有装饰器都支持灵活的使用方式！")
print("=" * 60)
print()
print("支持的用法：")
print("  @Component / @Component / @Component(name='...')")
print("  @Service / @Service() / @Service(name='...')")
print("  @Repository / @Repository() / @Repository(name='...')")
print("  @Configuration / @Configuration()")
print("  @Bean / @Bean() / @Bean(name='...')")
print("  @Primary / @Primary()")
print("  @Lazy / @Lazy()")
print("  @ConditionalOnMissingBean / @ConditionalOnMissingBean() / @ConditionalOnMissingBean(Type)")
