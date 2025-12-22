"""
PySpring - A SpringBoot-style scaffold for FastAPI with IoC and Auto-Configuration
"""

from . import core
from . import exception
from . import http
from . import interfaces
from . import ioc
# 导出主要模块以支持 IDE 识别
from . import log
from . import monitor
from . import repositories
from . import security
from . import system

__version__ = "1.0.0"

__all__ = [
    "log",
    "ioc",
    "core",
    "http",
    "security",
    "repositories",
    "interfaces",
    "exception",
    "system",
    "monitor",
    "__version__",
]
