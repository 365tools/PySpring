"""测试日志初始化流程"""

print("===== 开始测试 =====")
print("1. 导入 LoguruConfig")
from pyspring.log.providers.loguru.config.loader import LoguruConfig

print(f"   - configured={LoguruConfig.configured}")

print("\n2. 手动调用 setup_from_yaml()")
LoguruConfig.setup_from_yaml(force=False)
print(f"   - configured={LoguruConfig.configured}")

print("\n3. 导入 logger")
from pyspring.log.instance import logger

print(f"   - configured={LoguruConfig.configured}")

print("\n4. 尝试输出日志")
logger.info("这是一条INFO日志")
logger.warning("这是一条WARNING日志")
logger.error("这是一条ERROR日志")

print("\n5. 检查 loguru 实例")
from loguru import logger as raw_logger

print(f"   - _loguru handlers: {len(raw_logger._core.handlers)}")
