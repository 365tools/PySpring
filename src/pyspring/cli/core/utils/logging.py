import re
import sys
from contextlib import contextmanager
from typing import List

try:
    from loguru import logger
except ImportError:
    # Explicitly type as Any to avoid "variable has type Logger" conflict
    logger = None  # type: ignore


class OutputFilter:
    """Filter specific content from standard output stream"""

    def __init__(self, original_stream, patterns: List[str]):
        self.original_stream = original_stream
        self.patterns = [re.compile(p) for p in patterns]

    def write(self, data):
        # Fast path for suppressing everything
        for p in self.patterns:
            if p.pattern == r'.*':
                return

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
    # Note: Loguru sinks are hard to remove cleanly without impacting global state
    # This filter mainly targets stdout/stderr redirection.

    try:
        yield
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
