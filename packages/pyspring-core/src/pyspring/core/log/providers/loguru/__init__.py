"""
Loguru 日志提供者 - 延迟加载

不使用 import_package()，避免模块加载时全量拉取所有子模块
（middleware/config 等依赖 web/fastapi/ioc，全量导入会引入循环依赖并拖慢启动）。
需要的符号应该被显式导入（如 pyspring.log.providers.loguru.services.service）。
"""

__all__ = []
