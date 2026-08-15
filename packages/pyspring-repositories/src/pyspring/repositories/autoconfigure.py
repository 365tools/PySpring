"""pyspring-repositories starter 自动装配声明。"""

from __future__ import annotations

from pyspring.core.autoconfigure.declaration import StarterDeclaration


def load() -> StarterDeclaration:
    return StarterDeclaration(
        name="pyspring-repositories-starter",
        version="0.0.1",
        scan_packages=("pyspring.repositories",),
        auto_configuration=None,
        order=20,
        requires=("pyspring-core",),
    )


__all__ = ["load"]
