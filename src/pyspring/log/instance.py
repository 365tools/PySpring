from .manager import LogManager

# 获取由 LogManager 管理的实例（默认为 LoguruService）
# 保持向后兼容，但通过 Manager 获取确保单例一致性
logger = LogManager.get_logger()

__all__ = ["logger"]
