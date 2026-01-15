import re
import sys
from contextlib import contextmanager

from loguru import logger


class OutputFilter:
    """Filter specific content from standard output stream"""

    def __init__(self, original_stream, patterns):
        self.original_stream = original_stream
        self.patterns = [re.compile(p) for p in patterns]

    def write(self, data):
        # Skip if data contains matching pattern
        if any(p.search(data) for p in self.patterns):
            return
        self.original_stream.write(data)

    def flush(self):
        self.original_stream.flush()

    def __getattr__(self, name):
        return getattr(self.original_stream, name)


@contextmanager
def suppress_specific_logs():
    """Intercept and suppress specific log output"""
    # Log patterns to intercept
    patterns = [
        r"✅ 已加载日志配置",
        r"⚙️ Loguru日志系统统配置完成",
        r"\[SecurityConfigManager\] 已加载配置文件"  # Prevent output from security module
    ]

    # Replace standard streams
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    sys.stdout = OutputFilter(original_stdout, patterns)
    sys.stderr = OutputFilter(original_stderr, patterns)

    # Try to intercept Loguru sink
    try:
        # We cannot simply remove, because that would affect subsequent legitimate usage (if any)
        # But check operation is usually static, we choose to remove all sinks here, only keep our controllable ones (if needed)
        logger.remove()
    except ImportError:
        pass

    try:
        yield
    finally:
        # 恢复标准流
        sys.stdout = original_stdout
        sys.stderr = original_stderr
