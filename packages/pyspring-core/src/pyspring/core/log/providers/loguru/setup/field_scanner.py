"""
字段扫描器 - 扫描format字符串中的字段并自动注册

职责：防止format引用未定义的extra字段导致crash
"""
import re
from typing import Any, Set

from ..config.patcher import set_auto_injected_defaults, _CONTEXT_VARS_DEFINITIONS


class FieldScanner:
    """
    字段扫描器
    
    扫描配置中的format字符串，发现需要的extra字段，
    自动为缺失的字段注册默认值。
    """

    # Loguru保留关键字 + 自定义扩展字段
    RESERVED_KEYS = {
        'time', 'level', 'message', 'module', 'file', 'line', 'function',
        'name', 'process', 'thread', 'elapsed', 'exception', 'extra',
        'file_relative'  # PySpring自定义字段
    }

    @classmethod
    def scan_format_fields(cls, formats: list[str]) -> Set[str]:
        """
        扫描format字符串中使用的字段
        
        支持两种模式:
        - {extra[xxx]} - 显式extra字段
        - {xxx} - 泛型字段
        
        Args:
            formats: format字符串列表
            
        Returns:
            Set[str]: 需要的字段名集合
        """
        pattern_extra = re.compile(r'\{extra\[([a-zA-Z0-9_]+)\](?:[^}]*)?\}')
        pattern_generic = re.compile(r'\{([a-zA-Z0-9_]+)(?:[:!][^}]*)?\}')

        needed_keys = set()
        for fmt in formats:
            needed_keys.update(pattern_extra.findall(fmt))
            needed_keys.update(pattern_generic.findall(fmt))

        return needed_keys

    @classmethod
    def find_missing_fields(cls, needed: Set[str], active: Set[str]) -> Set[str]:
        """
        找出缺失的字段
        
        Args:
            needed: 需要的字段集合
            active: 已激活的字段集合
            
        Returns:
            Set[str]: 缺失的字段集合
        """
        # 合并已激活字段和保留字段
        all_active = active | cls.RESERVED_KEYS

        # 找出缺失的字段
        return needed - all_active

    @classmethod
    def register_defaults(cls, missing: Set[str]) -> None:
        """
        为缺失字段注册默认值
        
        Args:
            missing: 缺失的字段集合
        """
        if not missing:
            return

        auto_injected_defaults = {key: "N/A" for key in missing}
        set_auto_injected_defaults(auto_injected_defaults)

    @classmethod
    def auto_register_from_config(cls, logging_config: dict[str, Any]) -> None:
        """
        从配置中自动注册缺失的字段
        
        这是一个便捷方法，整合了扫描、查找和注册流程。
        
        Args:
            logging_config: 日志配置字典
        """
        # 1. 收集所有配置中使用的format字符串
        formats = []

        console_fmt = logging_config.get('console', {}).get('format')
        if console_fmt:
            formats.append(console_fmt)

        file_fmt = logging_config.get('file', {}).get('format')
        if file_fmt:
            formats.append(file_fmt)

        if not formats:
            return

        # 2. 扫描需要的字段
        needed_keys = cls.scan_format_fields(formats)

        # 3. 获取已激活的字段
        active_keys = {item[0] for item in _CONTEXT_VARS_DEFINITIONS}

        # 4. 找出缺失的字段
        missing_keys = cls.find_missing_fields(needed_keys, active_keys)

        # 5. 注册默认值
        cls.register_defaults(missing_keys)
