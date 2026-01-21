"""
全局日志实例

提供全局 logger 单例供应用使用。
"""
from .manager import LogManager

# 全局日志实例（默认为 LoguruService）
logger = LogManager.get_logger()

__all__ = ["logger"]
