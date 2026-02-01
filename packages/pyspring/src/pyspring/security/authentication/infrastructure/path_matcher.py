"""
路径匹配工具类
用于白名单路径匹配
"""
import re
from typing import List


class PathMatcher:
    """路径匹配器（支持通配符）"""

    @staticmethod
    def is_match(path: str, patterns: List[str]) -> bool:
        """
        检查路径是否匹配任意一个模式
        
        支持的模式：
        - 精确匹配: /api/login
        - 前缀匹配: /api/public/*
        - 通配符匹配: /api/*/info
        
        Args:
            path: 请求路径
            patterns: 匹配模式列表
            
        Returns:
            bool: 是否匹配
        """
        for pattern in patterns:
            if PathMatcher._match_pattern(path, pattern):
                return True
        return False

    @staticmethod
    def _match_pattern(path: str, pattern: str) -> bool:
        """
        单个模式匹配
        
        Args:
            path: 请求路径
            pattern: 匹配模式
            
        Returns:
            bool: 是否匹配
        """
        # 精确匹配
        if pattern == path:
            return True

        # 将通配符模式转换为正则表达式
        # * 匹配任意字符（除了 /）
        # ** 匹配任意字符（包括 /）
        regex_pattern = pattern.replace("**", "__DOUBLE_STAR__")
        regex_pattern = regex_pattern.replace("*", "[^/]*")
        regex_pattern = regex_pattern.replace("__DOUBLE_STAR__", ".*")
        regex_pattern = f"^{regex_pattern}$"

        return bool(re.match(regex_pattern, path))
