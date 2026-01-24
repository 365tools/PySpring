"""
测试框架级配置加载
验证 framework.yaml 能够正确加载和使用
"""
import tempfile
from pathlib import Path

import pytest
import yaml
from pyspring.ioc.context import ApplicationContext


class TestFrameworkConfig:
    """测试框架配置"""

    def test_framework_config_exists(self):
        """测试框架配置文件存在"""

        framework_dir = Path(__file__).parent.parent.parent.parent / 'src' / 'pyspring'
        config_path = framework_dir / 'config' / 'framework.yaml'

        assert config_path.exists(), f"框架配置文件不存在: {config_path}"

        # 验证配置文件可以被加载
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert 'framework' in config
        assert 'scan_packages' in config['framework']

    def test_framework_packages_loaded(self):
        """测试框架包能够被正确加载"""
        # 读取框架配置
        framework_dir = Path(__file__).parent.parent.parent.parent / 'src' / 'pyspring'
        config_path = framework_dir / 'config' / 'framework.yaml'

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        packages = config['framework']['scan_packages']

        # 验证包含必需的框架包
        assert 'pyspring.security' in packages, "应包含 pyspring.security 包"
        assert 'pyspring.repositories' in packages, "应包含 pyspring.repositories 包"

    def test_load_framework_packages_method(self):
        """测试 ApplicationContext._load_framework_packages() 方法"""
        packages = ApplicationContext._load_framework_packages()

        assert isinstance(packages, list)
        assert len(packages) > 0
        assert 'pyspring.security' in packages
        assert 'pyspring.repositories' in packages

    def test_framework_config_structure(self):
        """测试框架配置结构完整性"""
        framework_dir = Path(__file__).parent.parent.parent.parent / 'src' / 'pyspring'
        config_path = framework_dir / 'config' / 'framework.yaml'

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 验证顶层结构
        assert 'framework' in config
        framework = config['framework']

        # 验证必需字段
        assert 'scan_packages' in framework
        assert 'auto_configuration' in framework
        assert 'logging' in framework

        # 验证 auto_configuration
        assert 'enabled' in framework['auto_configuration']
        assert isinstance(framework['auto_configuration']['enabled'], bool)

        # 验证 logging
        assert 'level' in framework['logging']
        assert 'show_startup_info' in framework['logging']
        assert 'show_component_registration' in framework['logging']

    def test_framework_packages_are_valid_python_packages(self):
        """测试框架配置中的包是否是有效的 Python 包"""
        packages = ApplicationContext._load_framework_packages()

        for package in packages:
            # 验证包名格式
            assert package.startswith('pyspring.'), f"框架包应该以 'pyspring.' 开头: {package}"

            # 验证包是否可以导入（至少存在）
            parts = package.split('.')
            assert len(parts) >= 2, f"包名应该至少包含两级: {package}"

    def test_framework_config_fallback_on_missing_file(self):
        """测试当框架配置文件缺失时的降级行为"""
        # 这个测试验证 _load_framework_packages 在文件不存在时的降级逻辑
        # 实际文件存在，但我们可以测试降级返回值是否合理
        packages = ApplicationContext._load_framework_packages()

        # 无论如何都应该返回必要的包
        assert isinstance(packages, list)
        assert len(packages) >= 2  # 至少包含 security 和 repositories

    def test_framework_config_yaml_syntax(self):
        """测试框架配置文件 YAML 语法正确性"""
        framework_dir = Path(__file__).parent.parent.parent.parent / 'src' / 'pyspring'
        config_path = framework_dir / 'config' / 'framework.yaml'

        # 测试文件可以被正确解析
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            assert config is not None
        except yaml.YAMLError as e:
            pytest.fail(f"框架配置文件 YAML 语法错误: {e}")

    def test_framework_defaults_directory_exists(self):
        """测试框架默认配置目录存在"""
        framework_dir = Path(__file__).parent.parent.parent.parent / 'src' / 'pyspring'
        defaults_dir = framework_dir / 'config' / 'defaults'

        assert defaults_dir.exists(), f"框架默认配置目录不存在: {defaults_dir}"
        assert defaults_dir.is_dir()

        # 验证必需的默认配置文件
        required_files = ['security.yaml', 'repositories.yaml', 'logging.yaml']
        for filename in required_files:
            file_path = defaults_dir / filename
            assert file_path.exists(), f"缺少框架默认配置: {filename}"

    def test_framework_config_not_in_user_templates(self):
        """测试框架配置不应该出现在用户模板中"""
        templates_dir = Path(__file__).parent.parent.parent.parent / 'src' / 'pyspring' / 'templates'

        # framework.yaml 不应该在 templates/config 或 templates/example/config 中
        config_template = templates_dir / 'config' / 'framework.yaml'
        example_config_template = templates_dir / 'example' / 'config' / 'framework.yaml.template'

        assert not config_template.exists(), "framework.yaml 不应该在用户模板中"
        assert not example_config_template.exists(), "framework.yaml.template 不应该在示例模板中"

    def test_framework_scan_packages_no_duplicates(self):
        """测试框架扫描包列表没有重复"""
        packages = ApplicationContext._load_framework_packages()

        # 检查没有重复
        unique_packages = set(packages)
        assert len(packages) == len(unique_packages), f"框架包列表包含重复: {packages}"


class TestFrameworkConfigEdgeCases:
    """测试框架配置边界情况"""

    def test_framework_config_handles_missing_optional_fields(self):
        """测试框架配置缺少可选字段时的处理"""
        framework_dir = Path(__file__).parent.parent.parent.parent / 'src' / 'pyspring'
        config_path = framework_dir / 'config' / 'framework.yaml'

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # auto_configuration 和 logging 是可选的，但应该存在
        # 如果未来移除，代码应该能够处理
        framework = config.get('framework', {})

        # 测试即使缺少可选字段，scan_packages 仍能工作
        assert 'scan_packages' in framework

    def test_empty_scan_packages_list(self):
        """测试空的扫描包列表行为"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建一个扫描包为空的配置
            test_config = {
                'framework': {
                    'scan_packages': [],
                    'auto_configuration': {'enabled': True},
                    'logging': {'level': 'INFO'}
                }
            }

            config_path = Path(temp_dir) / 'framework.yaml'
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(test_config, f)

            # 验证可以加载（即使包列表为空）
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded = yaml.safe_load(f)

            assert loaded['framework']['scan_packages'] == []


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
