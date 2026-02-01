"""
健康检查管理器
"""

import time
from typing import List, Dict, Optional, Set

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

    def __init__(self, container=None, config: Optional[Dict] = None):
        """
        初始化健康检查管理器
        
        Args:
            container: IOC容器实例（可选）
            config: 健康检查配置（可选）
        """
        self.container = container
        self._indicators: List[HealthIndicator] = []
        self._config = config or {}
        self._enabled = self._config.get('enabled', True)
        self._enabled_indicator_names: Optional[Set[str]] = None

        # 解析启用的检查项
        if 'indicators' in self._config and self._config['indicators']:
            self._enabled_indicator_names = set(self._config['indicators'])

    def discover_indicators(self) -> None:
        """从IOC容器中自动发现所有HealthIndicator实例"""
        if not self._enabled:
            logger.debug("⏭️  健康检查已禁用（health.enabled=false）")
            return

        if not self.container:
            logger.warning("⚠️  IOC容器未设置，无法自动发现健康检查指标")
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
                                logger.debug(f"⏭️  跳过健康检查指标: {indicator_name}（未在配置中启用）")
                                continue

                        self._indicators.append(indicator)
                        logger.debug(f"🔍 发现健康检查指标: {indicator_name}")
                    except Exception as e:
                        logger.warning(f"⚠️  无法获取健康检查指标 {service_type.__name__}: {e}")

            # 检查配置中是否有不存在的检查项
            if self._enabled_indicator_names is not None:
                unknown_indicators = self._enabled_indicator_names - discovered_names
                if unknown_indicators:
                    logger.warning(
                        f"⚠️  配置中的健康检查指标未找到: {', '.join(unknown_indicators)}"
                    )

            # 按order排序
            self._indicators.sort(key=lambda x: x.order())

            if self._indicators:
                indicator_names = [ind.name() for ind in self._indicators]
                logger.debug(f"✅ 发现 {len(self._indicators)} 个健康检查指标: {', '.join(indicator_names)}")
            else:
                logger.debug("ℹ️  未发现任何健康检查指标")

        except Exception as e:
            logger.error(f"❌ 健康检查指标发现失败: {e}")

    def add_indicator(self, indicator: HealthIndicator) -> None:
        """
        手动添加健康检查指标
        
        Args:
            indicator: HealthIndicator实例
        """
        self._indicators.append(indicator)
        self._indicators.sort(key=lambda x: x.order())

    async def run_checks(self, parallel: bool = False) -> Dict[str, HealthCheckResult]:
        """
        执行所有健康检查（异步方法）
        
        Args:
            parallel: 是否并行执行（当前版本串行）
            
        Returns:
            Dict[str, HealthCheckResult]: 健康检查结果字典，key为指标名称
        """
        results = {}

        if not self._enabled:
            logger.debug("⏭️  健康检查已禁用")
            return results

        if not self._indicators:
            logger.debug("ℹ️  没有健康检查指标需要执行")
            return results

        logger.info(f"🔍 开始执行健康检查，共 {len(self._indicators)} 个指标...")

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
                                    logger.debug(f"    ✓ {key}:")
                                    for item in value:
                                        logger.debug(f"      • {item}")
                                else:
                                    logger.debug(f"    ✓ {key}: {value}")
                elif result.status == HealthStatus.DOWN:
                    logger.error(f"  {result} ({result.duration_ms:.2f}ms) - {result.error}")
                else:
                    logger.warning(f"  {result} ({result.duration_ms:.2f}ms)")

            except Exception as e:
                error_result = HealthCheckResult(
                    status=HealthStatus.UNKNOWN,
                    name=indicator.name(),
                    error=f"检查执行异常: {str(e)}"
                )
                results[indicator.name()] = error_result
                logger.error(f"  ❌ {indicator.name()}: 检查执行异常 - {e}")

        # 总结
        total = len(results)
        up_count = sum(1 for r in results.values() if r.status == HealthStatus.UP)
        down_count = sum(1 for r in results.values() if r.status == HealthStatus.DOWN)

        if down_count == 0:
            logger.info(f"✅ 健康检查完成: {up_count}/{total} 正常")
        else:
            logger.warning(f"⚠️  健康检查完成: {up_count}/{total} 正常, {down_count}/{total} 异常")

        return results

    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
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
    def indicators(self) -> List[HealthIndicator]:
        """获取所有已注册的健康检查指标"""
        return self._indicators.copy()
