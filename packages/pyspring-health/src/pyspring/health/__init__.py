"""PySpring Health Check starter。

提供标准化的健康检查协议和自动发现机制。
零依赖，独立安装即可用。
"""

from pyspring.health.indicator import HealthCheckResult, HealthIndicator, HealthStatus
from pyspring.health.manager import HealthCheckManager

__all__ = [
    'HealthIndicator',
    'HealthStatus',
    'HealthCheckResult',
    'HealthCheckManager',
]
