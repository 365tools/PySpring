"""pyspring-health starter 的自动装配声明。

health 模块零依赖（不依赖 pyspring 核心），独立安装即可用。
声明其装配顺序（order=40）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StarterDeclaration:
    """最小声明（避免依赖 pyspring-core，保持零依赖）。"""

    name: str
    version: str
    scan_packages: tuple[str, ...]
    order: int
    requires: tuple[str, ...]


def load() -> StarterDeclaration:
    """返回 health starter 的装配声明。"""
    return StarterDeclaration(
        name="pyspring-health-starter",
        version="0.0.1",
        scan_packages=(),
        order=40,
        requires=(),
    )


__all__ = ["load"]
