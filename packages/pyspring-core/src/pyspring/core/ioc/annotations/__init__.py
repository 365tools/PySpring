"""
IOC 注解包

提供所有 IOC 相关的装饰器注解。

包结构：
- component.py: 组件类装饰器（Component, Service, Repository）
- configuration.py: 配置类装饰器（Configuration, Bean）
- modifiers.py: 修饰器（Primary, Lazy）
- conditional.py: 条件装饰器（ConditionalOnMissingBean）
- scope.py: 作用域装饰器（Singleton, Prototype）
- utils.py: 装饰器工具函数（内部使用）
"""

# 导入所有装饰器，确保向后兼容
from pyspring.core.ioc.annotations.component import Component, Service, Repository
from pyspring.core.ioc.annotations.conditional import ConditionalOnMissingBean
from pyspring.core.ioc.annotations.configuration import Configuration, Bean
from pyspring.core.ioc.annotations.modifiers import Primary, Lazy
from pyspring.core.ioc.annotations.scope import Singleton, Prototype

__all__ = [
    # 组件装饰器
    'Component',
    'Service',
    'Repository',
    # 配置装饰器
    'Configuration',
    'Bean',
    # 修饰器
    'Primary',
    'Lazy',
    # 条件装饰器
    'ConditionalOnMissingBean',
    # 作用域装饰器
    'Singleton',
    'Prototype',
]
