"""
PySpring - A SpringBoot-style scaffold for FastAPI with IoC and Auto-Configuration
"""

from . import core
from . import web
from . import ioc
# ������Ҫģ����֧�� IDE ʶ��
from . import log
from . import repositories
from . import security

__version__ = "1.0.0"

__all__ = [
    "core",
    "web",
    "ioc",
    "log",
    "repositories",
    "security",
]

