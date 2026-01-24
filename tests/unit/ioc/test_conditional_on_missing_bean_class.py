"""
测试 @ConditionalOnMissingBean 装饰器对类的支持
"""
from pyspring.ioc.annotations.component import ConditionalOnMissingBean


class TestConditionalOnMissingBeanForClass:
    """测试 @ConditionalOnMissingBean 装饰类"""

    def test_conditional_class_is_marked_as_component(self):
        """测试使用 @ConditionalOnMissingBean 装饰的类会被自动标记为组件"""

        @ConditionalOnMissingBean(object)
        class TestConfig:
            pass

        # 验证类被标记为组件
        assert hasattr(TestConfig, "__pyspring_component__")
        assert getattr(TestConfig, "__pyspring_component__") is True

        # 验证条件属性也被设置
        assert hasattr(TestConfig, "__pyspring_conditional_on_missing_bean__")
        assert getattr(TestConfig, "__pyspring_conditional_on_missing_bean__") == object

    def test_conditional_class_without_imanaged_can_be_scanned(self):
        """测试不继承 IManaged 的条件类也能被扫描器识别"""
        from pyspring.ioc.scanner.scanner import ComponentScanner

        @ConditionalOnMissingBean(object)
        class PlainConfigClass:
            """普通配置类，不继承任何接口"""

            def __init__(self):
                self.value = "test"

        scanner = ComponentScanner()

        # 验证扫描器能够识别这个类为组件
        assert scanner._is_component(PlainConfigClass) is True

    def test_conditional_on_bean_method_still_works(self):
        """测试 @ConditionalOnMissingBean 装饰方法仍然正常工作"""
        from pyspring.ioc.annotations.component import Configuration, Bean

        @Configuration
        class TestConfig:
            @Bean()
            @ConditionalOnMissingBean(str)
            def default_string(self):
                return "default"

        # 验证方法被正确标记
        method = TestConfig.default_string
        assert hasattr(method, "__pyspring_bean__")
        assert hasattr(method, "__pyspring_conditional_on_missing_bean__")

        # 验证方法不会被标记为 component（只有类才标记）
        assert not hasattr(method, "__pyspring_component__")
