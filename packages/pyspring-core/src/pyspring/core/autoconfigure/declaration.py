"""Starter 自动装配声明。

一个 starter 通过包内资源 `pyspring-autoconfigure.json` 声明自身的装配信息：

```json
{
  "name": "pyspring-db-starter",
  "version": "0.0.1",
  "scan_packages": ["pyspring.repositories"],
  "auto_configuration": "pyspring.repositories.db_auto_config.DBAutoConfiguration",
  "order": 20,
  "requires": ["pyspring-core"]
}
```

`AutoConfigurationLoader` 读取该声明，决定是否装配该 starter。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StarterDeclaration:
    """单个 starter 的自动装配声明。"""

    name: str
    version: str = "0.0.1"
    scan_packages: tuple[str, ...] = ()
    auto_configuration: str | None = None
    order: int = 100
    requires: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("starter 声明必须包含 name")


def load_starter_declaration(payload: dict[str, Any]) -> StarterDeclaration:
    """从字典加载一个 starter 声明。

    Args:
        payload: `pyspring-autoconfigure.json` 解析后的字典。

    Returns:
        校验后的 StarterDeclaration。

    Raises:
        ValueError: 声明缺少必填字段或类型不合法。
    """
    name = payload.get("name")
    if not name or not isinstance(name, str):
        raise ValueError("starter 声明缺少合法的 name 字段")

    scan = payload.get("scan_packages", [])
    if not isinstance(scan, list):
        raise ValueError(f"starter {name} 的 scan_packages 必须是列表")

    requires = payload.get("requires", [])
    if not isinstance(requires, list):
        raise ValueError(f"starter {name} 的 requires 必须是列表")

    auto_config = payload.get("auto_configuration")
    if auto_config is not None and not isinstance(auto_config, str):
        raise ValueError(f"starter {name} 的 auto_configuration 必须是字符串")

    order = payload.get("order", 100)
    if not isinstance(order, int):
        order = 100

    return StarterDeclaration(
        name=name,
        version=str(payload.get("version", "0.0.1")),
        scan_packages=tuple(str(p) for p in scan),
        auto_configuration=auto_config,
        order=order,
        requires=tuple(str(r) for r in requires),
    )


def parse_declaration_json(raw: str) -> StarterDeclaration:
    """解析 `pyspring-autoconfigure.json` 的原始字符串。"""
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"无效的 pyspring-autoconfigure.json: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("pyspring-autoconfigure.json 顶层必须是 JSON 对象")
    return load_starter_declaration(payload)


__all__ = [
    "StarterDeclaration",
    "load_starter_declaration",
    "parse_declaration_json",
]
