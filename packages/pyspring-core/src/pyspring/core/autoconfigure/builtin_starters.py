"""内置模块 starter 声明。

当前 pyspring 仍为单包结构，security / repositories / web / health 等模块
尚未物理拆分为独立安装包。为验证 AutoConfiguration 机制，先将它们声明为
内置的"逻辑 starter"，通过 entry points 注册。

后续物理拆包时，这些声明会迁移到各自的独立 starter 包中。
"""

from __future__ import annotations

from pyspring.core.autoconfigure.declaration import StarterDeclaration


def security_starter() -> StarterDeclaration:
    return StarterDeclaration(
        name="pyspring-security-starter",
        version="0.0.1",
        scan_packages=("pyspring.security",),
        auto_configuration=None,
        order=10,
        requires=("pyspring-core",),
    )


def repositories_starter() -> StarterDeclaration:
    return StarterDeclaration(
        name="pyspring-repositories-starter",
        version="0.0.1",
        scan_packages=("pyspring.repositories",),
        auto_configuration=None,
        order=20,
        requires=("pyspring-core",),
    )


def web_starter() -> StarterDeclaration:
    return StarterDeclaration(
        name="pyspring-web-starter",
        version="0.0.1",
        scan_packages=("pyspring.web",),
        auto_configuration=None,
        order=30,
        requires=("pyspring-core",),
    )


__all__ = [
    "security_starter",
    "repositories_starter",
    "web_starter",
]
