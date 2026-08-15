"""
健康检查指标抽象接口和状态定义
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class HealthStatus(str, Enum):
    """健康状态枚举"""
    UP = "UP"  # 健康
    DOWN = "DOWN"  # 不健康
    UNKNOWN = "UNKNOWN"  # 未知
    OUT_OF_SERVICE = "OUT_OF_SERVICE"  # 服务停止


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: HealthStatus
    name: str
    details: dict[str, Any] = field(default_factory=dict)
    error: (str) | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0

    def __str__(self) -> str:
        marker = {
            HealthStatus.UP: "[UP]",
            HealthStatus.DOWN: "[DOWN]",
            HealthStatus.UNKNOWN: "[?]",
            HealthStatus.OUT_OF_SERVICE: "[SERVICE STOPPED]",
        }
        return f"{marker.get(self.status, '[?]')} {self.name}: {self.status.value}"


class HealthIndicator(ABC):
    """
    健康检查指标抽象基类
    
    实现此接口的类将被自动发现并执行健康检查
    
    Example:
        @Component
        class DatabaseHealthIndicator(HealthIndicator):
            def name(self) -> str:
                return "database"
            
            async def check(self) -> HealthCheckResult:
                try:
                    # 检查数据库连接
                    return HealthCheckResult(
                        status=HealthStatus.UP,
                        name=self.name(),
                        details={"connection": "active"}
                    )
                except Exception as e:
                    return HealthCheckResult(
                        status=HealthStatus.DOWN,
                        name=self.name(),
                        error=str(e)
                    )
    """

    @abstractmethod
    def name(self) -> str:
        """
        健康检查指标名称
        
        Returns:
            指标名称，如 "database", "cache", "disk" 等
        """
        pass

    @abstractmethod
    async def check(self) -> HealthCheckResult:
        """
        执行健康检查（异步方法）
        
        Returns:
            HealthCheckResult: 健康检查结果
        """
        pass

    def order(self) -> int:
        """
        检查执行顺序（数字越小越先执行）
        
        Returns:
            执行顺序，默认为0
        """
        return 0


__all__ = [
    "HealthStatus",
    "HealthCheckResult",
    "HealthIndicator",
]
