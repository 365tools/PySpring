"""
AOP 模块单元测试
"""
from pyspring.aop.facade import Aop


class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b


@Aop.aspect
class LoggingAspect:
    def __init__(self):
        self.log = []

    @Aop.before("add")
    def before_add(self, target, method_name, args, kwargs):
        self.log.append(f"before_{method_name}")

    @Aop.after("add")
    def after_add(self, target, method_name, result):
        self.log.append(f"after_{method_name}_{result}")

    @Aop.around("multiply")
    def around_multiply(self, proceed, target, method_name, args, kwargs):
        self.log.append("around_before")
        result = proceed()
        self.log.append(f"around_after_{result}")
        return result * 2  # 修改返回值

    @Aop.before("sub.*")
    def before_regex(self, target, method_name, args, kwargs):
        self.log.append(f"regex_before_{method_name}")


def test_aop_proxy_creation():
    """测试代理创建和基本方法调用"""
    calc = Calculator()
    aspect_inst = LoggingAspect()

    proxy = Aop.create_proxy(calc, [aspect_inst])

    # 验证代理对象不是原始对象
    assert proxy is not calc
    # 验证类型检查（通常代理应该看起来像原对象，或者是 duck typing）
    # 在这个简单实现中，isinstance(proxy, Calculator) 可能为 False，取决于 AopProxy 实现
    # 但我们至少确保能调用方法
    assert proxy.add(1, 2) == 3


def test_before_after_advice():
    """测试 Before 和 After 通知"""
    calc = Calculator()
    aspect_inst = LoggingAspect()
    proxy = Aop.create_proxy(calc, [aspect_inst])

    result = proxy.add(2, 3)

    assert result == 5
    assert "before_add" in aspect_inst.log
    assert "after_add_5" in aspect_inst.log
    # 确保调用顺序
    assert aspect_inst.log.index("before_add") < aspect_inst.log.index("after_add_5")


def test_around_advice():
    """测试 Around 通知"""
    calc = Calculator()
    aspect_inst = LoggingAspect()
    proxy = Aop.create_proxy(calc, [aspect_inst])

    # around advice 将结果翻倍
    result = proxy.multiply(3, 4)

    assert result == 24  # (3 * 4) * 2
    assert "around_before" in aspect_inst.log
    assert "around_after_12" in aspect_inst.log


def test_regex_pointcut():
    """测试正则匹配切入点"""
    calc = Calculator()
    aspect_inst = LoggingAspect()
    proxy = Aop.create_proxy(calc, [aspect_inst])

    result = proxy.subtract(5, 3)

    assert result == 2
    assert "regex_before_subtract" in aspect_inst.log


def test_no_match():
    """测试不匹配切入点的方法不受影响"""
    calc = Calculator()
    aspect_inst = LoggingAspect()
    proxy = Aop.create_proxy(calc, [aspect_inst])

    # 清空日志
    aspect_inst.log = []

    # multiply 只匹配了 around，没有匹配 before/after ("add")
    # subtract 匹配了 regex ("sub.*")

    # 我们加一个未被拦截的方法
    class AdvancedCalculator(Calculator):
        def divide(self, a, b):
            return a / b

    adv_calc = AdvancedCalculator()
    proxy_adv = Aop.create_proxy(adv_calc, [aspect_inst])

    result = proxy_adv.divide(10, 2)
    assert result == 5.0
    assert len(aspect_inst.log) == 0
