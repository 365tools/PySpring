"""PySpring AutoConfiguration 装配机制。

提供类似 Spring Boot `AutoConfiguration.imports` / `spring.factories` 的
声明式自动装配能力：

- 每个 starter 通过 Python entry point（`pyspring.starters`）注册自身。
- 启动时 `AutoConfigurationLoader` 发现所有已安装 starter，
  按 `order` 排序收集其需要扫描的框架包，实现"即插即用"。
- 未引入的 starter 完全不参与扫描，不影响核心功能。
"""

from pyspring.core.autoconfigure.loader import AutoConfiguration, AutoConfigurationLoader
from pyspring.core.autoconfigure.declaration import (
    StarterDeclaration,
    load_starter_declaration,
)

__all__ = [
    "AutoConfiguration",
    "AutoConfigurationLoader",
    "StarterDeclaration",
    "load_starter_declaration",
]
