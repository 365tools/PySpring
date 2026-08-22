"""
组件扫描器

负责扫描指定包路径，发现所有需要被IOC管理的组件
"""

import importlib
import inspect
import pkgutil
import traceback
from dataclasses import dataclass, field
from typing import Set

from pyspring.core.ioc.interfaces.core import IManaged
from pyspring.core.ioc.scanner.config import (
    DEFAULT_SCAN_CONFIG,
    ScanConfig,
    is_lifecycle_component,
)
from pyspring.core.log.instance import logger


@dataclass
class ComponentMetadata:
    """组件元数据"""

    cls: type  # 类型
    name: str  # 组件名称
    module: str  # 所属模块
    is_component: bool = False  # 是否是@Component
    is_configuration: bool = False  # 是否是@Configuration
    is_primary: bool = False  # 是否是主要候选者
    is_lazy: bool = False  # 是否懒加载
    bean_methods: list[str] = field(default_factory=list)  # Bean方法列表（仅Configuration）

    # 替换机制相关字段
    replaces: (str) | None = None  # 替换的组件名称（子类替换父类）
    replaced_by: (str) | None = None  # 被哪个组件替换（条件组件被替换）

    def __post_init__(self):
        if self.bean_methods is None:
            self.bean_methods = []


class ComponentScanner:
    """
    组件扫描器

    职责：
    1. 扫描指定包路径下的所有模块
    2. 识别需要被IOC管理的组件
    3. 提取组件的元数据
    4. 应用排除规则
    """

    def __init__(self, config: (ScanConfig) | None = None):
        self.config = config or DEFAULT_SCAN_CONFIG
        self.scanned_components: dict[type, ComponentMetadata] = {}
        self.scanned_modules: Set[str] = set()

        # 性能优化：缓存已处理的类信息
        self._processed_classes_cache: dict[str, bool] = {}

        # 类型映射表（用于替换检测）
        self.type_to_components: dict[type, list[ComponentMetadata]] = {}  # 类型 -> 组件列表
        self.conditional_components: dict[type, ComponentMetadata] = {}  # 条件类型 -> 条件组件

    def scan(self, base_packages: list[str]) -> dict[type, ComponentMetadata]:
        """
        扫描指定的包路径（两阶段扫描）

        阶段1: 扫描所有组件
        阶段2: 构建类型映射表
        阶段3: 检测替换关系

        Args:
            base_packages: 要扫描的包路径列表

        Returns:
            发现的组件字典 {类型: 元数据}
        """
        logger.debug(f"🔍 开始扫描组件，包路径: {base_packages}")

        # 阶段 1: 扫描所有组件
        for package_name in base_packages:
            self._scan_package(package_name)

        logger.debug(f"✅ 组件扫描完成，发现 {len(self.scanned_components)} 个组件")

        # 阶段 2: 构建类型映射表
        logger.debug("🔍 构建类型映射表...")
        self._build_type_mappings()

        # 阶段 3: 检测替换关系
        logger.debug("🔍 检测组件替换关系...")
        self._detect_replacements()

        return self.scanned_components

    def _scan_package(self, package_name: str):
        """扫描单个包"""
        try:
            # 导入包
            package = importlib.import_module(package_name)

            # 递归扫描子包
            if hasattr(package, "__path__"):
                for importer, modname, ispkg in pkgutil.walk_packages(
                    path=package.__path__, prefix=package.__name__ + ".", onerror=lambda x: None
                ):
                    # 检查是否应该扫描
                    if not self.config.should_scan_package(modname):
                        logger.debug(f"⏩ 跳过排除的包: {modname}")
                        continue

                    try:
                        self._scan_module(modname)
                    except Exception as e:
                        logger.error(f"❌ 扫描模块失败 {modname}: {e}")
                        raise
            else:
                # 单个模块
                self._scan_module(package_name)

        except ImportError as e:
            logger.error(f"❌ 无法导入包 {package_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ 扫描包时发生错误 {package_name}: {e}")
            raise

    def _scan_module(self, module_name: str):
        """扫描单个模块"""
        if module_name in self.scanned_modules:
            return

        self.scanned_modules.add(module_name)

        try:
            module = importlib.import_module(module_name)

            # 扫描模块中的所有类
            try:
                members = inspect.getmembers(module, inspect.isclass)
            except Exception as e:
                logger.error(f"❌ 获取模块成员失败 {module_name}: {e}")
                logger.error(f"调用栈:\n{traceback.format_exc()}")
                raise

            for name, obj in members:
                try:
                    # 只处理在当前模块中定义的类
                    if obj.__module__ != module_name:
                        continue

                    # 应用过滤规则
                    if not self._should_process_class(obj):
                        continue

                    # 提取元数据
                    metadata = self._extract_metadata(obj)
                    if metadata:
                        self.scanned_components[obj] = metadata
                        logger.debug(f"📦 发现组件: {name} ({module_name})")

                except Exception as e:
                    logger.error(f"❌ 处理类 {name} 时发生错误: {e}")
                    logger.error(f"调用栈:\n{traceback.format_exc()}")
                    raise

        except Exception as e:
            logger.error(f"❌ 扫描模块 {module_name} 时发生错误: {e}")
            logger.error(f"调用栈:\n{traceback.format_exc()}")
            raise

    def _should_process_class(self, cls: type) -> bool:
        """判断是否应该处理该类"""
        # 使用缓存避免重复计算
        class_key = f"{cls.__module__}.{cls.__name__}"
        if class_key in self._processed_classes_cache:
            return self._processed_classes_cache[class_key]

        # 1. 检查是否是Protocol（接口定义）
        if getattr(cls, "_is_protocol", False):
            result = False

        # 2. 检查是否是抽象类（有未实现的抽象方法）
        elif not self.config.scan_abstract:
            if self._is_unimplemented_abstract_class(cls):
                result = False
            else:
                # 3. 应用配置的过滤规则
                if not self.config.should_scan_class(cls):
                    result = False
                else:
                    # 4. 排除生命周期组件（Initializer/Handler）
                    if is_lifecycle_component(cls):
                        logger.debug(f"⏩ 跳过生命周期组件: {cls.__name__}")
                        result = False
                    else:
                        # 5. 检查是否有组件标记
                        result = self._is_component(cls)
        else:
            # 如果配置允许扫描抽象类，跳过前面的抽象类检查
            # 3. 应用配置的过滤规则
            if not self.config.should_scan_class(cls):
                result = False
            else:
                # 4. 排除生命周期组件（Initializer/Handler）
                if is_lifecycle_component(cls):
                    logger.debug(f"⏩ 跳过生命周期组件: {cls.__name__}")
                    result = False
                else:
                    # 5. 检查是否有组件标记
                    result = self._is_component(cls)

        # 缓存结果
        self._processed_classes_cache[class_key] = result
        return result

    def _is_unimplemented_abstract_class(self, cls: type) -> bool:
        """
        检查是否是未实现的抽象类

        Args:
            cls: 待检查的类

        Returns:
            如果是未实现的抽象类则返回True，否则返回False
        """
        # 检查是否存在未实现的抽象方法
        abstract_methods = getattr(cls, "__abstractmethods__", None)
        return abstract_methods is not None and len(abstract_methods) > 0

    def _is_component(self, cls: type) -> bool:
        """判断类是否是组件"""
        # 显式标记 @Component
        if hasattr(cls, "__pyspring_component__"):
            return True

        # 显式标记 @Configuration
        if hasattr(cls, "__pyspring_configuration__"):
            return True

        # 实现了 IManaged 接口
        try:
            if IManaged in cls.__mro__:
                return True
        except TypeError, AttributeError:
            pass

        return False

    def _extract_metadata(self, cls: type) -> (ComponentMetadata) | None:
        """提取组件元数据"""
        try:
            # 基本信息
            name = getattr(cls, "__pyspring_name__", self._generate_name(cls))
            module = cls.__module__

            # 标记
            is_component = hasattr(cls, "__pyspring_component__")
            is_configuration = hasattr(cls, "__pyspring_configuration__")
            is_primary = getattr(cls, "__pyspring_primary__", False)
            is_lazy = getattr(cls, "__pyspring_lazy__", False)

            # 扫描Bean方法（仅Configuration）
            bean_methods = []
            if is_configuration:
                bean_methods = self._scan_bean_methods(cls)

            return ComponentMetadata(
                cls=cls,
                name=name,
                module=module,
                is_component=is_component,
                is_configuration=is_configuration,
                is_primary=is_primary,
                is_lazy=is_lazy,
                bean_methods=bean_methods,
            )

        except Exception as e:
            logger.error(f"❌ 提取元数据失败 {cls.__name__}: {e}")
            return None

    def _scan_bean_methods(self, cls: type) -> list[str]:
        """扫描配置类中的Bean方法"""
        bean_methods = []
        try:
            for name, method in inspect.getmembers(cls, inspect.isfunction):
                if hasattr(method, "__pyspring_bean__"):
                    bean_methods.append(name)
                    logger.debug(f"  🌱 发现Bean方法: {name}")
        except Exception as e:
            logger.error(f"❌ 扫描Bean方法失败 {cls.__name__}: {e}")
            logger.error(f"调用栈:\n{traceback.format_exc()}")
            raise
        return bean_methods

    def _build_type_mappings(self):
        """构建类型映射表"""
        for comp_type, metadata in self.scanned_components.items():
            # 为每个类型（包括所有基类）添加映射
            for base_class in comp_type.__mro__:
                if base_class is object:
                    continue
                self.type_to_components.setdefault(base_class, []).append(metadata)

            # 记录条件组件
            conditional_type = getattr(comp_type, "__pyspring_conditional_on_missing_bean__", None)
            if conditional_type is not None:
                # 如果未指定类型或指定为 object，使用组件自身类型
                if conditional_type is None or conditional_type is object:
                    conditional_type = comp_type

                # 记录条件组件映射
                if conditional_type not in self.conditional_components:
                    self.conditional_components[conditional_type] = metadata
                    logger.debug(f"  📌 条件组件: {metadata.name} (检查类型: {conditional_type.__name__})")

    def _detect_replacements(self):
        """检测组件替换关系（基于继承）"""
        replacement_count = 0

        for comp_type, metadata in self.scanned_components.items():
            # 跳过已被标记为替换其他组件的
            if metadata.replaces:
                continue

            # 检查所有基类（跳过自己和 object）
            for base_class in comp_type.__mro__[1:]:
                if base_class is object:
                    continue

                # 如果基类是条件组件
                if base_class in self.conditional_components:
                    conditional_meta = self.conditional_components[base_class]

                    # 避免自己替换自己
                    if conditional_meta.cls == comp_type:
                        continue

                    # 标记替换关系
                    metadata.replaces = conditional_meta.name
                    conditional_meta.replaced_by = metadata.name
                    replacement_count += 1

                    logger.info(
                        f"🔄 检测到替换: {metadata.name} ({comp_type.__name__}) "
                        f"替换 {conditional_meta.name} ({base_class.__name__})"
                    )
                    break  # 只替换最近的条件基类

        if replacement_count > 0:
            logger.debug(f"✅ 检测到 {replacement_count} 个组件替换")

    @staticmethod
    def _generate_name(service_type: type) -> str:
        """生成组件名称（类名转snake_case）"""
        import re

        name = service_type.__name__
        # CamelCase -> snake_case
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        return name


__all__ = ["ComponentScanner", "ComponentMetadata"]
