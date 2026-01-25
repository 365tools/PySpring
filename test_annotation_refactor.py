"""
测试注解包重构后的导入和功能

验证：
1. 从主包导入所有装饰器
2. 所有装饰器功能正常
3. 向后兼容性
"""
import os
import sys

# 添加 src 路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_imports():
    """测试所有装饰器可以正常导入"""
    print("=" * 60)
    print("测试 1: 从主包导入所有装饰器")
    print("=" * 60)

    try:
        from pyspring.ioc.annotations import (
            Component, Service, Repository,
            Configuration, Bean,
            Primary, Lazy,
            ConditionalOnMissingBean,
            Singleton, Prototype
        )
        print("✅ 所有装饰器导入成功")
        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_submodule_imports():
    """测试从子模块导入"""
    print("\n" + "=" * 60)
    print("测试 2: 从子模块导入装饰器")
    print("=" * 60)

    try:
        from pyspring.ioc.annotations.component import Component, Service, Repository
        from pyspring.ioc.annotations.configuration import Configuration, Bean
        from pyspring.ioc.annotations.modifiers import Primary, Lazy
        from pyspring.ioc.annotations.conditional import ConditionalOnMissingBean
        print("✅ 所有子模块导入成功")
        return True
    except ImportError as e:
        print(f"❌ 子模块导入失败: {e}")
        return False


def test_decorator_functionality():
    """测试装饰器功能"""
    print("\n" + "=" * 60)
    print("测试 3: 装饰器功能测试")
    print("=" * 60)

    from pyspring.ioc.annotations import (
        Component, Service, Configuration, Bean,
        Primary, Lazy,
        ConditionalOnMissingBean
    )

    # 测试 Component（不带括号）
    @Component
    class TestService1:
        pass

    assert hasattr(TestService1, "__pyspring_component__")
    print("✅ @Component (不带括号) 正常工作")

    # 测试 Component（带括号）
    @Component(name="test_service", primary=True)
    class TestService2:
        pass

    assert hasattr(TestService2, "__pyspring_component__")
    assert hasattr(TestService2, "__pyspring_name__")
    assert hasattr(TestService2, "__pyspring_primary__")
    print("✅ @Component(参数) 正常工作")

    # 测试 Service
    @Service
    class MyService:
        pass

    assert hasattr(MyService, "__pyspring_component__")
    print("✅ @Service 正常工作")

    # 测试 Configuration
    @Configuration
    class AppConfig:
        pass

    assert hasattr(AppConfig, "__pyspring_configuration__")
    print("✅ @Configuration 正常工作")

    # 测试 Bean（不带括号）
    @Configuration
    class BeanConfig:
        @Bean
        def my_bean(self):
            return "test"

    assert hasattr(BeanConfig.my_bean, "__pyspring_bean__")
    print("✅ @Bean (不带括号) 正常工作")

    # 测试 Bean（带参数）
    @Configuration
    class BeanConfig2:
        @Bean(name="custom_bean")
        def my_bean(self):
            return "test"

    assert hasattr(BeanConfig2.my_bean, "__pyspring_bean__")
    assert hasattr(BeanConfig2.my_bean, "__pyspring_bean_name__")
    print("✅ @Bean(参数) 正常工作")

    # 测试 Primary
    @Primary
    class PrimaryBean:
        pass

    assert hasattr(PrimaryBean, "__pyspring_primary__")
    print("✅ @Primary 正常工作")

    # 测试 Lazy
    @Lazy
    class LazyBean:
        pass

    assert hasattr(LazyBean, "__pyspring_lazy__")
    print("✅ @Lazy 正常工作")

    # 测试 ConditionalOnMissingBean（不带括号）
    @ConditionalOnMissingBean
    class ConditionalBean1:
        pass

    assert hasattr(ConditionalBean1, "__pyspring_conditional_on_missing_bean__")
    assert hasattr(ConditionalBean1, "__pyspring_component__")  # 自动标记为组件
    print("✅ @ConditionalOnMissingBean (不带括号) 正常工作")

    # 测试 ConditionalOnMissingBean（带括号）
    @ConditionalOnMissingBean()
    class ConditionalBean2:
        pass

    assert hasattr(ConditionalBean2, "__pyspring_conditional_on_missing_bean__")
    print("✅ @ConditionalOnMissingBean() 正常工作")

    return True


def test_combined_decorators():
    """测试组合使用装饰器"""
    print("\n" + "=" * 60)
    print("测试 4: 装饰器组合使用")
    print("=" * 60)

    from pyspring.ioc.annotations import Component, Primary, Lazy
    from pyspring.ioc.annotations.scope import Singleton, Scope

    @Component
    @Primary
    @Lazy
    @Singleton
    class CombinedService:
        pass

    assert hasattr(CombinedService, "__pyspring_component__")
    assert hasattr(CombinedService, "__pyspring_primary__")
    assert hasattr(CombinedService, "__pyspring_lazy__")
    assert hasattr(CombinedService, "__pyspring_scope__")
    assert CombinedService.__pyspring_scope__ == Scope.SINGLETON
    print("✅ 装饰器组合使用正常")

    return True


def main():
    """运行所有测试"""
    print("开始测试 PySpring 注解包重构...")
    print()

    results = []

    # 运行测试
    results.append(("主包导入", test_imports()))
    results.append(("子模块导入", test_submodule_imports()))
    results.append(("装饰器功能", test_decorator_functionality()))
    results.append(("装饰器组合", test_combined_decorators()))

    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("\n🎉 所有测试通过！注解包重构成功！")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
