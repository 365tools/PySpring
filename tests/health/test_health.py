"""
pyspring-health：健康检查测试

验证独立 health starter 的核心能力：
- 健康状态枚举
- 健康检查结果
- 健康指标抽象
- 健康检查管理器（发现、执行、聚合）
"""
import asyncio

import pytest

from pyspring.health import HealthCheckManager, HealthIndicator, HealthStatus, HealthCheckResult


class DummyContainer:
    """模拟容器：提供已注册类型和获取服务"""
    def __init__(self, indicator):
        self._indicator = indicator

    def get_all_registered_types(self):
        return [type(self._indicator)]

    def get_service(self, service_type):
        return self._indicator


class DummyIndicator(HealthIndicator):
    """测试用健康指标"""
    def __init__(self, name="dummy", status=HealthStatus.UP):
        self._name = name
        self._status = status

    def name(self) -> str:
        return self._name

    async def check(self):
        return HealthCheckResult(
            status=self._status,
            name=self.name(),
            details={"ok": True},
        )


class TestHealthStatus:
    """健康状态枚举"""

    def test_status_values(self):
        assert HealthStatus.UP == "UP"
        assert HealthStatus.DOWN == "DOWN"
        assert HealthStatus.UNKNOWN == "UNKNOWN"


class TestHealthCheckResult:
    """健康检查结果"""

    def test_result_creation(self):
        result = HealthCheckResult(status=HealthStatus.UP, name="db")
        assert result.status == HealthStatus.UP
        assert result.name == "db"
        assert result.details == {}

    def test_result_str(self):
        result = HealthCheckResult(status=HealthStatus.UP, name="db")
        assert "UP" in str(result)


class TestHealthCheckManager:
    """健康检查管理器"""

    def test_discover_indicators(self):
        """测试自动发现健康指标"""
        manager = HealthCheckManager(container=DummyContainer(DummyIndicator()))
        manager.discover_indicators()
        assert len(manager.indicators) == 1
        assert manager.indicators[0].name() == "dummy"

    def test_add_indicator_manually(self):
        """测试手动添加指标"""
        manager = HealthCheckManager()
        manager.add_indicator(DummyIndicator(name="manual"))
        assert manager.indicators[0].name() == "manual"

    def test_run_checks(self):
        """测试执行健康检查"""
        manager = HealthCheckManager(container=DummyContainer(DummyIndicator()))
        manager.discover_indicators()

        results = asyncio.run(manager.run_checks())
        assert "dummy" in results
        assert results["dummy"].status == HealthStatus.UP

    def test_overall_status_up(self):
        """测试整体状态：全部 UP 时返回 UP"""
        results = {
            "a": HealthCheckResult(status=HealthStatus.UP, name="a"),
            "b": HealthCheckResult(status=HealthStatus.UP, name="b"),
        }
        manager = HealthCheckManager()
        assert manager.get_overall_status(results) == HealthStatus.UP

    def test_overall_status_down(self):
        """测试整体状态：有 DOWN 时返回 DOWN"""
        results = {
            "a": HealthCheckResult(status=HealthStatus.UP, name="a"),
            "b": HealthCheckResult(status=HealthStatus.DOWN, name="b", error="boom"),
        }
        manager = HealthCheckManager()
        assert manager.get_overall_status(results) == HealthStatus.DOWN
