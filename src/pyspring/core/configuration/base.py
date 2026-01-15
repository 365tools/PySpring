"""
配置基类 (Proxy)

Forwarding to abstracts.config to avoid circular dependencies.
"""
from pyspring.core.abstracts.config import (
    ConfigBase,
    ConfigSection,
    ConfigMetadata,
    TConfig
)

__all__ = [
    "ConfigBase",
    "ConfigSection",
    "ConfigMetadata",
    "TConfig",
]
