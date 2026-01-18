import re
import sys
from contextlib import contextmanager
from typing import List

try:
    from loguru import logger
except ImportError:
    logger = None


class OutputFilter:
    """Filter specific content from standard output stream"""

    def __init__(self, original_stream, patterns: List[str]):
        self.original_stream = original_stream
        self.patterns = [re.compile(p) for p in patterns]

    def write(self, data):
        if any(p.search(data) for p in self.patterns):
            return
        self.original_stream.write(data)

    def flush(self):
        self.original_stream.flush()

    def __getattr__(self, name):
        return getattr(self.original_stream, name)


@contextmanager
def suppress_logs(patterns: List[str] = None):
    """
    Intercept and suppress specific log output matching patterns.
    
    Args:
        patterns: List of regex strings to suppress.
    """
    if patterns is None:
        patterns = []

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    sys.stdout = OutputFilter(original_stdout, patterns)
    sys.stderr = OutputFilter(original_stderr, patterns)

    # Try to intercept Loguru sink if available
    if logger:
        try:
            logger.remove()
        except Exception:
            pass

    try:
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
