"""
日志过滤器 - 根据配置过滤日志记录

提供灵活的日志过滤功能，支持健康检查、指标、静态资源等常见过滤需求。
"""
from typing import Dict, Any


def filter_logs(record, logging_config: Dict[str, Any]) -> bool:
    """
    根据配置过滤日志记录
    
    Args:
        record: Loguru 日志记录对象
        logging_config: 日志配置字典
        
    Returns:
        bool: True 表示保留日志，False 表示过滤掉
    """
    message = record.get("message", "").lower()

    # 获取过滤器配置
    filters_config = logging_config.get('filters', {})

    # 根据配置进行过滤
    filter_rules = [
        (filters_config.get('health_check', True), "health"),
        (filters_config.get('metrics', True), "metrics"),
        (filters_config.get('favicon', True), "favicon.ico"),
    ]

    for filter_enabled, keyword in filter_rules:
        if filter_enabled and keyword in message:
            return False

    # 检查自定义过滤路径
    custom_paths = filters_config.get('custom_paths', [])
    for path in custom_paths:
        if path.lower() in message:
            return False

    return True


__all__ = ["filter_logs"]
