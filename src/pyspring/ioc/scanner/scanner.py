"""
组件扫描器

负责扫描指定包路径，发现所有需要被IOC管理的组件
"""
import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from typing import List, Set, Dict, Optional

from pyspring.ioc.interfaces.core import IManaged
from pyspring.ioc.scanner.config import ScanConfig, DEFAULT_SCAN_CONFIG, is_lifecycle_component
from pyspring.log.instance import logger


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
    bean_methods: List[str] = None  # Bean方法列表（仅Configuration）

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

    def __init__(self, config: Optional[ScanConfig] = None):
        self.config = config or DEFAULT_SCAN_CONFIG
        self.scanned_components: Dict[type, ComponentMetadata] = {}
        self.scanned_modules: Set[str] = set()

    def scan(self, base_packages: List[str]) -> Dict[type, ComponentMetadata]:
        """
        扫描指定的包路径
        
        Args:
            base_packages: 要扫描的包路径列表
            
        Returns:
            发现的组件字典 {类型: 元数据}
        """
        logger.info(f"🔍 开始扫描组件，包路径: {base_packages}")

        for package_name in base_packages:
            self._scan_package(package_name)

        logger.info(f"✅ 组件扫描完成，发现 {len(self.scanned_components)} 个组件")
        return self.scanned_components

    def _scan_package(self, package_name: str):
        """扫描单个包"""
        try:
            # 导入包
            package = importlib.import_module(package_name)

            # 递归扫描子包
            if hasattr(package, '__path__'):
                for importer, modname, ispkg in pkgutil.walk_packages(
                        path=package.__path__,
                        prefix=package.__name__ + '.',
                        onerror=lambda x: None
                ):
                    # 检查是否应该扫描
                    if not self.config.should_scan_package(modname):
                        logger.debug(f"⏩ 跳过排除的包: {modname}")
                        continue

                    try:
                        self._scan_module(modname)
                    except Exception as e:
                        logger.warning(f"⚠️ 扫描模块失败 {modname}: {e}")
            else:
                # 单个模块
                self._scan_module(package_name)

        except ImportError as e:
            logger.error(f"❌ 无法导入包 {package_name}: {e}")
        except Exception as e:
            logger.error(f"❌ 扫描包时发生错误 {package_name}: {e}")

    def _scan_module(self, module_name: str):
        """扫描单个模块"""
        if module_name in self.scanned_modules:
            return

        self.scanned_modules.add(module_name)

        try:
            module = importlib.import_module(module_name)

            # 扫描模块中的所有类
            for name, obj in inspect.getmembers(module, inspect.isclass):
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
            logger.debug(f"⚠️ 扫描模块 {module_name} 时发生错误: {e}")

    def _should_process_class(self, cls: type) -> bool:
        """判断是否应该处理该类"""
        # 1. 检查是否是Protocol（接口定义）
        if getattr(cls, '_is_protocol', False):
            return False

        # 2. 检查是否是抽象类
        if inspect.isabstract(cls) and not self.config.scan_abstract:
            return False

        # 3. 应用配置的过滤规则
        if not self.config.should_scan_class(cls):
            return False

        # 4. 排除生命周期组件（Initializer/Handler）
        if is_lifecycle_component(cls):
            logger.debug(f"⏩ 跳过生命周期组件: {cls.__name__}")
            return False

        # 5. 检查是否有组件标记
        if not self._is_component(cls):
            return False

        return True

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
        except (TypeError, AttributeError):
            pass

        return False

    def _extract_metadata(self, cls: type) -> Optional[ComponentMetadata]:
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
                bean_methods=bean_methods
            )

        except Exception as e:
            logger.error(f"❌ 提取元数据失败 {cls.__name__}: {e}")
            return None

    def _scan_bean_methods(self, cls: type) -> List[str]:
        """扫描配置类中的Bean方法"""
        bean_methods = []
        for name, method in inspect.getmembers(cls, inspect.isfunction):
            if hasattr(method, "__pyspring_bean__"):
                bean_methods.append(name)
                logger.debug(f"  🌱 发现Bean方法: {name}")
        return bean_methods

    @staticmethod
    def _generate_name(cls: type) -> str:
        """生成组件名称（类名转snake_case）"""
        import re
        name = cls.__name__
        # CamelCase -> snake_case
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        return name


__all__ = ['ComponentScanner', 'ComponentMetadata']
