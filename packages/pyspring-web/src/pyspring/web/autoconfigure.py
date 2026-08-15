"""pyspring-web starter 自动装配声明。"""

from __future__ import annotations

from pyspring.core.autoconfigure.declaration import StarterDeclaration


def load() -> StarterDeclaration:
    return StarterDeclaration(
        name="pyspring-web",
        version="0.0.1",
        scan_packages=("pyspring.web",),
        auto_configuration=None,
        order=30,
        requires=("pyspring-core",),
    )


__all__ = ["load"]
