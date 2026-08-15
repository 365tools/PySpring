"""
健康检查管理器
"""

import time
from typing import Set, cast

from loguru import logger

from .indicator import HealthIndicator, HealthCheckResult, HealthStatus


class HealthCheckManager:
    """
    健康检查管理器
    
    负责：
    1. 自动发现所有HealthIndicator实例
    2. 根据配置过滤要执行的检查
    3. 按顺序执行健康检查
    4. 聚合检查结果
    """

    def __init__(self, container=None, config: dict[str, object] | None = None):
        """
        初始化健康检查管理器
        
        Args:
            container: IOC容器实例（可选）
            config: 健康检查配置（可选）
        """
        self.container = container
        self._indicators: list[HealthIndicator] = []
        self._config = config or {}
        self._enabled = self._config.get('enabled', True)
        self._enabled_indicator_names: (Set[str]) | None = None

        # 解析启用的检查项
        if 'indicators' in self._config and self._config['indicators']:
            self._enabled_indicator_names = set(cast(list[str], self._config['indicators']))

    def discover_indicators(self) -> None:
        """从IOC容器中自动发现所有HealthIndicator实例"""
        if not self._enabled:
            logger.debug("[skip] Health checks disabled (health.enabled=false)")
            return

        if not self.container:
            logger.warning("[!] IOC container not set, cannot auto-discover health indicators")
            return

        try:
            # 获取所有注册的服务类型
            all_services = self.container.get_all_registered_types()
            discovered_names = set()

            for service_type in all_services:
                # 检查是否实现了HealthIndicator接口
                if issubclass(service_type, HealthIndicator):
                    try:
                        indicator = self.container.get_service(service_type)
                        indicator_name = indicator.name()
                        discovered_names.add(indicator_name)

                        # 根据配置过滤
                        if self._enabled_indicator_names is not None:
                            if indicator_name not in self._enabled_indicator_names:
                                logger.debug(f"[skip] Skip health indicator: {indicator_name} (not enabled in config)")
                                continue

                        self._indicators.append(indicator)
                        logger.debug(f"[search] Found health indicator: {indicator_name}")
                    except Exception as e:
                        logger.warning(f"[!] Failed to get health indicator {service_type.__name__}: {e}")

            # 检查配置中是否有不存在的检查项
            if self._enabled_indicator_names is not None:
                unknown_indicators = self._enabled_indicator_names - discovered_names
                if unknown_indicators:
                    logger.warning(
                        f"[!] Health indicators from config not found: {', '.join(unknown_indicators)}"
                    )

            # 按order排序
            self._indicators.sort(key=lambda x: x.order())

            if self._indicators:
                indicator_names = [ind.name() for ind in self._indicators]
                logger.debug(f"[OK] Found {len(self._indicators)} health indicators: {', '.join(indicator_names)}")
            else:
                logger.debug("[i] No health indicators found")

        except Exception as e:
            logger.error(f"[X] Health indicator discovery failed: {e}")

    def add_indicator(self, indicator: HealthIndicator) -> None:
        """
        手动添加健康检查指标
        
        Args:
            indicator: HealthIndicator实例
        """
        self._indicators.append(indicator)
        self._indicators.sort(key=lambda x: x.order())

    async def run_checks(self, parallel: bool = False) -> dict[str, HealthCheckResult]:
        """
        执行所有健康检查（异步方法）
        
        Args:
            parallel: 是否并行执行（当前版本串行）
            
        Returns:
            dict[str, HealthCheckResult]: 健康检查结果字典，key为指标名称
        """
        results = {}

        if not self._enabled:
            logger.debug("[skip] Health checks disabled")
            return results

        if not self._indicators:
            logger.debug("[i] No health indicators to run")
            return results

        logger.info(f"[search] Running {len(self._indicators)} health indicators...")

        for indicator in self._indicators:
            try:
                start_time = time.time()
                result = await indicator.check()
                result.duration_ms = (time.time() - start_time) * 1000

                results[result.name] = result

                # 输出日志
                if result.status == HealthStatus.UP:
                    logger.info(f"  {result} ({result.duration_ms:.2f}ms)")
                    # 显示重要的details信息
                    if result.details:
                        for key, value in result.details.items():
                            if key in ['verified', 'endpoint_test', 'framework_check']:
                                if isinstance(value, list):
                                    logger.debug(f"    [+] {key}:")
                                    for item in value:
                                        logger.debug(f"      - {item}")
                                else:
                                    logger.debug(f"    [+] {key}: {value}")
                elif result.status == HealthStatus.DOWN:
                    logger.error(f"  {result} ({result.duration_ms:.2f}ms) - {result.error}")
                else:
                    logger.warning(f"  {result} ({result.duration_ms:.2f}ms)")

            except Exception as e:
                error_result = HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    name=indicator.name(),
                    error=f"Check execution error: {str(e)}"
                )
                results[indicator.name()] = error_result
                logger.error(f"  [X] {indicator.name()}: check execution error - {e}")

        # 总结
        total = len(results)
        up_count = sum(1 for r in results.values() if r.status == HealthStatus.UP)
        down_count = sum(1 for r in results.values() if r.status == HealthStatus.DOWN)

        if down_count == 0:
            logger.info(f"[OK] Health checks completed: {up_count}/{total} healthy")
        else:
            logger.warning(f"[!] Health checks completed: {up_count}/{total} healthy, {down_count}/{total} unhealthy")

        return results

    def get_overall_status(self, results: dict[str, HealthCheckResult]) -> HealthStatus:
        """
        获取整体健康状态
        
        Args:
            results: 健康检查结果字典
            
        Returns:
            HealthStatus: 整体健康状态
        """
        if not results:
            return HealthStatus.UNKNOWN

        # 只要有一个DOWN，整体就是DOWN
        if any(r.status == HealthStatus.DOWN for r in results.values()):
            return HealthStatus.DOWN

        # 如果都是UP，整体就是UP
        if all(r.status == HealthStatus.UP for r in results.values()):
            return HealthStatus.UP

        # 其他情况返回UNKNOWN
        return HealthStatus.UNKNOWN

    @property
    def indicators(self) -> list[HealthIndicator]:
        """获取所有已注册的健康检查指标"""
        return self._indicators.copy()


__all__ = [
    "HealthCheckManager",
]
