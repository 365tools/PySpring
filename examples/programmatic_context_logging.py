"""
本示例演示如何通过代码编程方式注册上下文变量，
替代 tedious 的 YAML 配置。
"""
import os
import sys
import uuid
from contextvars import ContextVar

# 添加 src 到路径以便直接运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from pyspring.log import logger
from pyspring.log.core.registry import register_context_var

# 1. 定义你的业务上下文变量
trace_id_ctx = ContextVar("trace_id", default=None)

# 2. 在应用启动时注册它
# 这样 Loguru 就会自动尝试从 trace_id_ctx 获取值并在日志中显示
# 如果 user 未设置 trace_id，则显示 default (这里设为 "no-trace")
register_context_var("trace_id", trace_id_ctx, default="no-trace")

# 更新 logger 格式以显示 trace_id (通常在 config/logging.yaml 中根据需要调整 format)
# 这里为了演示效果，我们临时修改一下 console handler
try:
    from loguru import logger as _loguru
    from pyspring.log.providers.loguru.config.formatter import LoguruConfig

    _loguru.remove()  # 移除旧的

    # 注意：现在不需要手动添加 filter，全局 patcher 会自动处理上下文注入
    _loguru.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | trace:<cyan>{extra[trace_id]}</cyan> | <level>{message}</level>",
        level="INFO"
    )
except Exception as e:
    print(f"Error reconfiguring logger: {e}")


def process_request():
    # 3. 在业务中使用 ContextVar
    token = trace_id_ctx.set(str(uuid.uuid4())[:8])
    try:
        # 下面的日志会自动带上 trace_id
        logger.info("Handling request user=123")
        logger.warning("Something minor happened")
    finally:
        trace_id_ctx.reset(token)


def main():
    logger.info("System startup (no trace context yet)")

    process_request()

    logger.info("System shutdown")


if __name__ == "__main__":
    main()