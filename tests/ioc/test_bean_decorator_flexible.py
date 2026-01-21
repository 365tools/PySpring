#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试Bean装饰器的灵活用法（支持有参和无参）"""

import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent.parent.parent / 'src'
sys.path.insert(0, str(src_path))

from pyspring.ioc.annotations.component import Bean, Configuration


@Configuration
class FlexibleBeanConfig:
    """测试Bean装饰器的多种用法"""

    @Bean  # 用法1: 不加括号（像@staticmethod）
    def method_without_parens(self):
        """不加括号的Bean"""
        return "method1"

    @Bean()  # 用法2: 空括号
    def method_with_empty_parens(self):
        """空括号的Bean"""
        return "method2"

    @Bean(name="custom_name")  # 用法3: 带name参数
    def method_with_name(self):
        """带自定义名称的Bean"""
        return "method3"

    @Bean(init_method="init", destroy_method="cleanup")  # 用法4: 带生命周期方法
    def method_with_lifecycle(self):
        """带生命周期方法的Bean"""
        return "method4"

    @Bean(name="full_config", init_method="setup", destroy_method="teardown")  # 用法5: 所有参数
    def method_with_all_params(self):
        """所有参数的Bean"""
        return "method5"


def test_bean_without_parentheses():
    """测试@Bean（不加括号）"""
    method = FlexibleBeanConfig.method_without_parens
    assert hasattr(method, '__pyspring_bean__'), "@Bean 应该设置 __pyspring_bean__ 属性"
    assert getattr(method, '__pyspring_bean__') is True
    print("✅ @Bean (不加括号) - 通过")


def test_bean_with_empty_parentheses():
    """测试@Bean()（空括号）"""
    method = FlexibleBeanConfig.method_with_empty_parens
    assert hasattr(method, '__pyspring_bean__'), "@Bean() 应该设置 __pyspring_bean__ 属性"
    assert getattr(method, '__pyspring_bean__') is True
    print("✅ @Bean() (空括号) - 通过")


def test_bean_with_name():
    """测试@Bean(name=...)"""
    method = FlexibleBeanConfig.method_with_name
    assert hasattr(method, '__pyspring_bean__'), "应该有 __pyspring_bean__ 属性"
    assert getattr(method, '__pyspring_bean__') is True
    assert hasattr(method, '__pyspring_bean_name__'), "应该有 __pyspring_bean_name__ 属性"
    assert getattr(method, '__pyspring_bean_name__') == 'custom_name', "Bean名称应该是 'custom_name'"
    print("✅ @Bean(name='custom_name') - 通过")


def test_bean_with_lifecycle():
    """测试@Bean(init_method=..., destroy_method=...)"""
    method = FlexibleBeanConfig.method_with_lifecycle
    assert hasattr(method, '__pyspring_bean__'), "应该有 __pyspring_bean__ 属性"
    assert getattr(method, '__pyspring_bean__') is True
    assert hasattr(method, '__pyspring_init_method__'), "应该有 __pyspring_init_method__ 属性"
    assert getattr(method, '__pyspring_init_method__') == 'init', "init_method 应该是 'init'"
    assert hasattr(method, '__pyspring_destroy_method__'), "应该有 __pyspring_destroy_method__ 属性"
    assert getattr(method, '__pyspring_destroy_method__') == 'cleanup', "destroy_method 应该是 'cleanup'"
    print("✅ @Bean(init_method=..., destroy_method=...) - 通过")


def test_bean_with_all_params():
    """测试@Bean的所有参数组合"""
    method = FlexibleBeanConfig.method_with_all_params
    assert hasattr(method, '__pyspring_bean__')
    assert getattr(method, '__pyspring_bean__') is True
    assert getattr(method, '__pyspring_bean_name__') == 'full_config'
    assert getattr(method, '__pyspring_init_method__') == 'setup'
    assert getattr(method, '__pyspring_destroy_method__') == 'teardown'
    print("✅ @Bean(name=..., init_method=..., destroy_method=...) - 通过")


def main():
    """运行所有测试"""
    print("=" * 80)
    print("Bean装饰器灵活用法测试")
    print("=" * 80)
    print()

    try:
        test_bean_without_parentheses()
        test_bean_with_empty_parentheses()
        test_bean_with_name()
        test_bean_with_lifecycle()
        test_bean_with_all_params()

        print()
        print("=" * 80)
        print("总结: @Bean 现在像 @staticmethod 一样灵活！")
        print("  - @Bean          ✅ 支持（不加括号）")
        print("  - @Bean()        ✅ 支持（空括号）")
        print("  - @Bean(...)     ✅ 支持（带参数）")
        print("=" * 80)
        print()
        print("✅ 所有测试通过！")

    except AssertionError as e:
        print()
        print("=" * 80)
        print(f"❌ 测试失败: {e}")
        print("=" * 80)
        raise


if __name__ == '__main__':
    main()
