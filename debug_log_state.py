"""调试日志系统状态"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

print("1. 导入 LoguruConfig")
from pyspring.log.providers.loguru.config.loader import LoguruConfig

print(f"   - configured={LoguruConfig.configured}")

print("\n2. 导入 logger")
from pyspring.log.instance import logger

print(f"   - configured={LoguruConfig.configured}")

print("\n3. 尝试输出日志")
logger.info("测试INFO")
logger.warning("测试WARNING")
logger.error("测试ERROR")

print("\n4. 检查 loguru 实例")
from loguru import logger as _loguru

print(f"   - _loguru handlers: {len(_loguru._core.handlers)}")
for h_id, h in _loguru._core.handlers.items():
    print(f"     Handler {h_id}: {h}")
