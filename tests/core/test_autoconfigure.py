"""
pyspring-core：AutoConfiguration 装配测试

验证拆包后的 starter 声明式装配机制：
- 通过 entry points 发现所有已安装 starter
- 按 order 排序
- 收集各 starter 的扫描包
"""
from pyspring.core.autoconfigure.loader import AutoConfigurationLoader


class TestAutoConfigurationLoader:
    """AutoConfiguration 装配器测试"""

    def test_discover_all_starters(self):
        """测试发现所有已安装的 starter"""
        loader = AutoConfigurationLoader()
        configs = loader.discover()

        names = [c.name for c in configs]
        # 至少包含核心 starter
        assert 'pyspring-core' in names

    def test_order_sorted(self):
        """测试 starter 按 order 升序排列"""
        loader = AutoConfigurationLoader()
        configs = loader.discover()

        orders = [c.order for c in configs]
        assert orders == sorted(orders)

    def test_collect_scan_packages(self):
        """测试收集扫描包（去重保序）"""
        loader = AutoConfigurationLoader()
        packages = loader.collect_scan_packages()

        assert isinstance(packages, list)
        # 去重检查
        assert len(packages) == len(set(packages))

    def test_core_has_lowest_order(self):
        """测试 core starter 最先装配（order 最低）"""
        loader = AutoConfigurationLoader()
        configs = loader.discover()

        core_configs = [c for c in configs if c.name == 'pyspring-core']
        if core_configs:
            assert core_configs[0].order == min(c.order for c in configs)
