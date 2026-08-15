"""
组件扫描配置

定义扫描的包、排除规则等
"""
import re
from dataclasses import dataclass, field
from typing import Set, Pattern


@dataclass
class ScanConfig:
    """扫描配置"""

    # 要扫描的包路径列表
    base_packages: list[str] = field(default_factory=list)

    # 排除的包路径模式
    excluded_packages: Set[str] = field(default_factory=lambda: {
        'pyspring.repositories.providers',  # Repository提供者实现
        'pyspring.*.test',  # 测试代码
        'pyspring.*.tests',  # 测试代码
    })

    # 排除的类名模式（正则表达式）
    excluded_class_patterns: list[Pattern[str]] = field(default_factory=lambda: [
        re.compile(r'.*Test$'),  # 测试类
        re.compile(r'.*Mock$'),  # Mock类
        re.compile(r'^Base.*'),  # Base开头的抽象类
        re.compile(r'.*Abstract.*'),  # Abstract类
        re.compile(r'.*Interface$'),  # Interface后缀
        re.compile(r'^I[A-Z].*'),  # I开头的接口（如IUserService）
    ])

    # 排除的特定类型
    excluded_base_types: Set[type] = field(default_factory=set)

    # 是否扫描抽象类
    scan_abstract: bool = False

    # 是否扫描Protocol类
    scan_protocols: bool = False

    def should_scan_package(self, module_path: str) -> bool:
        """判断是否应该扫描该包"""
        for excluded in self.excluded_packages:
            if excluded in module_path:
                return False
        return True

    def should_scan_class(self, cls: type) -> bool:
        """判断是否应该扫描该类"""
        # 检查类名模式
        class_name = cls.__name__
        for pattern in self.excluded_class_patterns:
            if pattern.match(class_name):
                return False

        # 检查基类
        if self.excluded_base_types:
            for base_type in self.excluded_base_types:
                try:
                    if issubclass(cls, base_type):
                        return False
                except TypeError:
                    pass

        return True


# 默认配置
DEFAULT_SCAN_CONFIG = ScanConfig()

# Initializer专用排除规则（不应该被扫描为普通组件）
LIFECYCLE_EXCLUDED_TYPES = {
    'IStartupInitializer',
    'IShutdownHandler',
    'IConnectionInitializer',
    'IMigrationInitializer',
}


def is_lifecycle_component(cls: type) -> bool:
    """
    判断是否是生命周期组件基类（应该被排除扫描）
    
    注意：只排除基类接口本身，不排除实现类
    例如：排除 IStartupInitializer，但不排除 DatabaseInitializer
    """
    class_name = cls.__name__

    # 只排除生命周期接口基类本身，不排除实现类
    if class_name in LIFECYCLE_EXCLUDED_TYPES:
        return True

    return False


__all__ = ['ScanConfig', 'DEFAULT_SCAN_CONFIG', 'is_lifecycle_component']
