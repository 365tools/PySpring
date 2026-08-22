"""AutoConfiguration 装配器。

核心职责：
1. 通过 Python entry points（group = `pyspring.starters`）发现所有已安装的 starter。
2. 每个 starter 的 entry point 指向一个加载器（函数或可调用对象），
   返回 `StarterDeclaration`，声明其扫描包、自动配置类、装配顺序等。
3. 按 `order` 排序，收集所有 starter 需要扫描的框架包。

这是对 `framework.yaml` 集中式硬编码扫描的替代：
- 引入 starter 即自动发现（即插即用）。
- 未引入的 starter 完全不参与扫描（不引用不影响核心）。
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from typing import Any, Callable, Iterable

from pyspring.core.autoconfigure.declaration import StarterDeclaration

# entry point group：所有 PySpring starter 都注册在此组下
ENTRY_POINT_GROUP = "pyspring.starters"

# 始终加载的核心 starter（对应 spring-core）
CORE_STARTER_NAME = "pyspring-core"


@dataclass(frozen=True)
class AutoConfiguration:
    """已解析的 starter 自动装配结果。"""

    name: str
    scan_packages: tuple[str, ...]
    order: int
    auto_configuration: str | None
    requires: tuple[str, ...] = ()

    @classmethod
    def from_declaration(cls, declaration: StarterDeclaration) -> "AutoConfiguration":
        return cls(
            name=declaration.name,
            scan_packages=declaration.scan_packages,
            order=declaration.order,
            auto_configuration=declaration.auto_configuration,
            requires=declaration.requires,
        )


class AutoConfigurationLoader:
    """发现并排序所有已安装 starter 的自动装配声明。"""

    def __init__(self, entry_point_group: str = ENTRY_POINT_GROUP) -> None:
        self._entry_point_group = entry_point_group

    def discover(self) -> list[AutoConfiguration]:
        """发现所有已安装 starter，并按 order 升序返回。

        通过 importlib.metadata 扫描 `pyspring.starters` entry point group。
        每个 entry point 的 value 指向一个加载函数，调用后返回
        `StarterDeclaration`。
        """
        configs: list[AutoConfiguration] = []
        for entry_point in self._iter_entry_points():
            declaration = self._load_declaration(entry_point)
            if declaration is None:
                continue
            configs.append(AutoConfiguration.from_declaration(declaration))

        # 按 order 升序排序（core=0 最先装配）
        configs.sort(key=lambda cfg: cfg.order)
        return configs

    def collect_scan_packages(self) -> list[str]:
        """收集所有已发现 starter 的扫描包（按 order 排序，去重保序）。"""
        packages: list[str] = []
        seen: set[str] = set()
        for config in self.discover():
            for pkg in config.scan_packages:
                if pkg not in seen:
                    seen.add(pkg)
                    packages.append(pkg)
        return packages

    def validate_requires(self, configs: list[AutoConfiguration]) -> list[str]:
        """校验所有 starter 声明的 `requires` 依赖是否都已安装。

        对标 Spring 的 starter 依赖解析：缺失依赖的 starter 会明确报错，
        而不是静默装配后运行时才失败。

        Returns:
            缺失依赖的描述列表；空列表表示全部满足。
        """
        installed = {c.name for c in configs}
        missing: list[str] = []
        for config in configs:
            for req in config.requires:
                if req not in installed:
                    missing.append(f"starter '{config.name}' 声明依赖 '{req}'，但未安装")
        return missing

    def load_auto_configuration(self, config: AutoConfiguration) -> type | None:
        """导入并返回 starter 声明的 AutoConfiguration 配置类。

        `auto_configuration` 字段声明了 starter 的 `@Configuration` 自动配置类
        （用于注册默认 Bean）。本方法验证该配置类可被导入，使得声明真正生效。

        Args:
            config: 已解析的 starter 自动装配结果。

        Returns:
            AutoConfiguration 配置类；若未声明或导入失败返回 None。
        """
        if not config.auto_configuration:
            return None
        try:
            module_path, _, attr = config.auto_configuration.rpartition(".")
            if not module_path or not attr:
                return None
            import importlib

            module = importlib.import_module(module_path)
            config_cls = getattr(module, attr, None)
            return config_cls if isinstance(config_cls, type) else None
        except ImportError, AttributeError:
            return None

    def _iter_entry_points(self) -> Iterable[metadata.EntryPoint]:
        try:
            return metadata.entry_points(group=self._entry_point_group)
        except TypeError:
            # 兼容旧版 importlib.metadata API（Python < 3.10）
            eps = metadata.entry_points()
            if hasattr(eps, "select"):
                return eps.select(group=self._entry_point_group)
            return [ep for ep in eps if ep.group == self._entry_point_group]

    def _load_declaration(self, entry_point: metadata.EntryPoint) -> StarterDeclaration | None:
        """调用 entry point 加载器获取 starter 声明。

        entry point 的 value 形如 `module:callable`，`callable()` 返回
        `StarterDeclaration` 或可转换为声明的字典。
        """
        loader: Callable[[], Any] | None = None
        try:
            loader = entry_point.load()
        except ImportError, AttributeError:
            loader = None

        if loader is None:
            return None

        try:
            result = loader()
        except Exception:
            return None

        if isinstance(result, StarterDeclaration):
            return result
        if isinstance(result, dict):
            return self._coerce_declaration(
                name=result.get("name"),
                version=result.get("version"),
                scan_packages=result.get("scan_packages"),
                auto_configuration=result.get("auto_configuration"),
                order=result.get("order"),
                requires=result.get("requires"),
            )
        # 鸭子类型：任何具备 name/scan_packages/order 属性的对象（不同包自定义的声明类）
        if hasattr(result, "name") and hasattr(result, "scan_packages"):
            return self._coerce_declaration(
                name=getattr(result, "name"),
                version=getattr(result, "version", None),
                scan_packages=getattr(result, "scan_packages", ()),
                auto_configuration=getattr(result, "auto_configuration", None),
                order=getattr(result, "order", None),
                requires=getattr(result, "requires", ()),
            )
        return None

    @staticmethod
    def _coerce_declaration(
        name: object,
        version: object,
        scan_packages: object,
        auto_configuration: object,
        order: object,
        requires: object,
    ) -> StarterDeclaration | None:
        """将任意来源的声明字段统一转换为本包 StarterDeclaration。"""
        if not name or not isinstance(name, str):
            return None
        from pyspring.core.autoconfigure.declaration import load_starter_declaration

        payload: dict[str, Any] = {"name": name}
        if version is not None:
            payload["version"] = version
        if isinstance(scan_packages, (list, tuple)):
            payload["scan_packages"] = list(scan_packages)
        elif isinstance(scan_packages, str):
            payload["scan_packages"] = [scan_packages]
        if auto_configuration is not None:
            payload["auto_configuration"] = auto_configuration
        if isinstance(order, int):
            payload["order"] = order
        if isinstance(requires, (list, tuple)):
            payload["requires"] = list(requires)

        try:
            return load_starter_declaration(payload)
        except ValueError:
            return None


__all__ = [
    "AutoConfiguration",
    "AutoConfigurationLoader",
    "ENTRY_POINT_GROUP",
    "CORE_STARTER_NAME",
]
