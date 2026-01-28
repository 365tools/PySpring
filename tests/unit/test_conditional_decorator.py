"""
测试 @ConditionalOnMissingBean 装饰器的不同使用方式
"""
from pyspring.ioc.annotations.component import Component, ConditionalOnMissingBean

print("=" * 60)
print("测试 @ConditionalOnMissingBean 装饰器")
print("=" * 60)
print()

# 测试1: 不带括号 + @Component
print("测试1: @Component + @ConditionalOnMissingBean (不带括号)")
try:
    @Component
    @ConditionalOnMissingBean
    class TestClass1:
        pass


    print(f"✅ TestClass1 类型: {type(TestClass1)}")
    print(f"   是否是类: {isinstance(TestClass1, type)}")
    print(f"   __pyspring_component__: {hasattr(TestClass1, '__pyspring_component__')}")
    print(f"   __pyspring_conditional_on_missing_bean__: {hasattr(TestClass1, '__pyspring_conditional_on_missing_bean__')}")
    if hasattr(TestClass1, '__pyspring_conditional_on_missing_bean__'):
        print(f"   条件类型: {getattr(TestClass1, '__pyspring_conditional_on_missing_bean__')}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback

    traceback.print_exc()

print()

# 测试2: 带括号 + @Component
print("测试2: @Component + @ConditionalOnMissingBean() (带括号)")
try:
    @Component
    @ConditionalOnMissingBean()
    class TestClass2:
        pass


    print(f"✅ TestClass2 类型: {type(TestClass2)}")
    print(f"   是否是类: {isinstance(TestClass2, type)}")
    print(f"   __pyspring_component__: {hasattr(TestClass2, '__pyspring_component__')}")
    print(f"   __pyspring_conditional_on_missing_bean__: {hasattr(TestClass2, '__pyspring_conditional_on_missing_bean__')}")
    if hasattr(TestClass2, '__pyspring_conditional_on_missing_bean__'):
        print(f"   条件类型: {getattr(TestClass2, '__pyspring_conditional_on_missing_bean__')}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback

    traceback.print_exc()

print()

# 测试3: 指定类型 + @Component
print("测试3: @Component + @ConditionalOnMissingBean(SomeType)")
try:
    from abc import ABC, abstractmethod


    class SomeInterface(ABC):
        @abstractmethod
        def do_something(self):
            pass


    @Component
    @ConditionalOnMissingBean(SomeInterface)
    class TestClass3(SomeInterface):
        def do_something(self):
            return "test"


    print(f"✅ TestClass3 类型: {type(TestClass3)}")
    print(f"   是否是类: {isinstance(TestClass3, type)}")
    print(f"   __pyspring_component__: {hasattr(TestClass3, '__pyspring_component__')}")
    print(f"   __pyspring_conditional_on_missing_bean__: {hasattr(TestClass3, '__pyspring_conditional_on_missing_bean__')}")
    if hasattr(TestClass3, '__pyspring_conditional_on_missing_bean__'):
        bean_type = getattr(TestClass3, '__pyspring_conditional_on_missing_bean__')
        print(f"   条件类型: {bean_type}")
        print(f"   条件类型是 SomeInterface: {bean_type is SomeInterface}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback

    traceback.print_exc()

print()

# 测试4: 只用 @ConditionalOnMissingBean 不带括号（自动添加 @Component）
print("测试4: @ConditionalOnMissingBean (不带括号，无 @Component)")
try:
    @ConditionalOnMissingBean
    class TestClass4:
        pass


    print(f"✅ TestClass4 类型: {type(TestClass4)}")
    print(f"   是否是类: {isinstance(TestClass4, type)}")
    print(f"   __pyspring_component__: {hasattr(TestClass4, '__pyspring_component__')}")
    print(f"   __pyspring_conditional_on_missing_bean__: {hasattr(TestClass4, '__pyspring_conditional_on_missing_bean__')}")
    if hasattr(TestClass4, '__pyspring_conditional_on_missing_bean__'):
        print(f"   条件类型: {getattr(TestClass4, '__pyspring_conditional_on_missing_bean__')}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback

    traceback.print_exc()

print()

# 测试5: 只用 @ConditionalOnMissingBean 带括号（自动添加 @Component）
print("测试5: @ConditionalOnMissingBean() (带括号，无 @Component)")
try:
    @ConditionalOnMissingBean()
    class TestClass5:
        pass


    print(f"✅ TestClass5 类型: {type(TestClass5)}")
    print(f"   是否是类: {isinstance(TestClass5, type)}")
    print(f"   __pyspring_component__: {hasattr(TestClass5, '__pyspring_component__')}")
    print(f"   __pyspring_conditional_on_missing_bean__: {hasattr(TestClass5, '__pyspring_conditional_on_missing_bean__')}")
    if hasattr(TestClass5, '__pyspring_conditional_on_missing_bean__'):
        print(f"   条件类型: {getattr(TestClass5, '__pyspring_conditional_on_missing_bean__')}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback

    traceback.print_exc()

print()

# 测试6: 测试框架中的实际类
print("测试6: 导入框架中的 SecurityEntityConfiguration")
try:
    from pyspring.security.authentication.config.entity import SecurityEntityConfiguration

    print(f"✅ SecurityEntityConfiguration 类型: {type(SecurityEntityConfiguration)}")
    print(f"   是否是类: {isinstance(SecurityEntityConfiguration, type)}")
    print(f"   __pyspring_component__: {hasattr(SecurityEntityConfiguration, '__pyspring_component__')}")
    print(f"   __pyspring_conditional_on_missing_bean__: {hasattr(SecurityEntityConfiguration, '__pyspring_conditional_on_missing_bean__')}")
    if hasattr(SecurityEntityConfiguration, '__pyspring_conditional_on_missing_bean__'):
        print(f"   条件类型: {getattr(SecurityEntityConfiguration, '__pyspring_conditional_on_missing_bean__')}")
except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback

    traceback.print_exc()

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
