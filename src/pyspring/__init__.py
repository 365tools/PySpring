"""
PySpring - A SpringBoot-style scaffold for FastAPI with IoC and Auto-Configuration
"""
from utils.auto_import import auto_import_package

__version__ = "1.0.0"

__all__ = auto_import_package(__name__, globals())
