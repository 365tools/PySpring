"""
Check utility functions
"""
import re
import sys
from contextlib import contextmanager

from loguru import logger


class OutputFilter:
    """过滤标准输出流中的特定内容"""

    def __init__(self, original_stream, patterns):
        self.original_stream = original_stream
        self.patterns = [re.compile(p) for p in patterns]

    def write(self, data):
        # 如果数据包含匹配的模式，则跳过
        if any(p.search(data) for p in self.patterns):
            return
        self.original_stream.write(data)

    def flush(self):
        self.original_stream.flush()

    def __getattr__(self, name):
        return getattr(self.original_stream, name)


@contextmanager
def suppress_specific_logs():
    """拦截并抑制特定的日志输出"""
    # 需要拦截的日志模式
    patterns = [
        r"✅ 已加载日志配置",
        r"⚙️ Loguru日志系统统配置完成",
        r"\[SecurityConfigManager\] 已加载配置文件"  # 防止安全模块的输出
    ]

    # 替换标准流
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    sys.stdout = OutputFilter(original_stdout, patterns)
    sys.stderr = OutputFilter(original_stderr, patterns)

    # 尝试拦截 Loguru 的 sink
    try:
        # 我们不能简单移除，因为那样会影响后续可能的合法使用（虽然 check 本身可能不需要）
        # 但 check 一般是静态的，我们这里选择移除所有 sink，只保留我们自己可控的（如果需要）
        logger.remove()
    except ImportError:
        pass

    try:
        yield
    finally:
        # 恢复标准流
        sys.stdout = original_stdout
        sys.stderr = original_stderr
