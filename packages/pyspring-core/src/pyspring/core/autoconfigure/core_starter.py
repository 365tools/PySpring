"""pyspring-core 核心 starter 的自动装配声明。

核心 starter 始终随框架加载，对应 Spring 的 `spring-core`。
它不扫描额外框架包（核心包 `pyspring.ioc/aop/log/config` 由框架自身提供），
主要用于声明装配顺序为 0（最先装配）。
"""

from __future__ import annotations

from pyspring.core.autoconfigure.declaration import StarterDeclaration


def load() -> StarterDeclaration:
    """返回核心 starter 的装配声明。"""
    return StarterDeclaration(
        name="pyspring-core",
        version="0.0.1",
        scan_packages=(),
        auto_configuration=None,
        order=0,
        requires=(),
    )


__all__ = ["load"]
