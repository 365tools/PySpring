"""
依赖信息类

用于描述服务依赖的各种信息
"""
from dataclasses import dataclass
from typing import Any, Type


@dataclass
class DependencyInfo:
    """
    依赖信息
    
    描述一个服务依赖的各种属性
    """
    param_name: str  # 参数名称
    param_type: type  # 参数类型
    service_name: str  # 服务名称（空字符串表示按类型查找）
    qualifier: (str) | None = None  # 限定符
    is_list: bool = False  # 是否是列表注入
    element_type: Type[Any] | None = None  # 列表元素类型（仅当is_list为True时有效）
