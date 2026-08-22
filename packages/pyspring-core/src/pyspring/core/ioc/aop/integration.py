"""
AOP代理集成

为服务自动创建AOP代理
"""

import inspect
from typing import Any

from pyspring.core.log.instance import logger


class AopIntegration:
    """
    AOP集成

    自动为带有切面的服务创建代理
    """

    def __init__(self, container):
        self.container = container
        self._aspect_cache = {}

    def should_create_proxy(self, service_type: type) -> bool:
        """
        判断是否需要为服务创建代理

        Args:
            service_type: 服务类型

        Returns:
            bool: 是否需要代理
        """
        # 检查类或方法上是否有切面注解
        if hasattr(service_type, "__pyspring_aspects__"):
            return True

        # 检查方法上是否有切面
        for name, method in inspect.getmembers(service_type, inspect.isfunction):
            if hasattr(method, "__pyspring_pointcut__"):
                return True

        return False

    def create_proxy(self, target: Any, service_type: type) -> Any:
        """
        为目标对象创建AOP代理

        Args:
            target: 目标对象
            service_type: 服务类型

        Returns:
            代理对象或原对象
        """
        if not self.should_create_proxy(service_type):
            return target

        try:
            # 收集切面
            aspects = self._collect_aspects(service_type)
            if not aspects:
                return target

            # 导入AOP代理工厂
            from pyspring.core.aop.proxy.factory import create_proxy

            proxy = create_proxy(target, aspects)
            logger.debug(f"🎯 为服务 {service_type.__name__} 创建AOP代理")
            return proxy

        except ImportError:
            logger.warning("⚠️  AOP模块未安装，跳过代理创建")
            return target
        except Exception as e:
            logger.error(f"❌ 创建AOP代理失败: {e}")
            return target

    def _collect_aspects(self, service_type: type) -> list[Any]:
        """
        收集服务的切面

        Args:
            service_type: 服务类型

        Returns:
            切面列表
        """
        aspects = []

        # 从类注解获取切面
        if hasattr(service_type, "__pyspring_aspects__"):
            aspect_types = service_type.__pyspring_aspects__
            for aspect_type in aspect_types:
                aspect = self._get_aspect_instance(aspect_type)
                if aspect:
                    aspects.append(aspect)

        return aspects

    def _get_aspect_instance(self, aspect_type: type) -> (Any) | None:
        """
        获取切面实例（使用容器管理）

        Args:
            aspect_type: 切面类型

        Returns:
            切面实例
        """
        # 尝试从容器获取
        try:
            return self.container.get_by_type(aspect_type)
        except Exception:
            # 如果容器中没有，尝试直接实例化
            try:
                return aspect_type()
            except Exception as e:
                logger.error(f"无法实例化切面 {aspect_type.__name__}: {e}")
                return None


__all__ = ["AopIntegration"]
