"""
日志系统使用示例

展示如何使用 PySpring 的日志系统
"""
from pyspring.log.instance import logger


def basic_logging_example():
    """基础日志示例"""
    print("\n=== 基础日志示例 ===")

    # 不同级别的日志
    logger.trace("这是追踪日志（最详细）")
    logger.debug("这是调试日志")
    logger.info("这是信息日志")
    logger.success("这是成功日志")
    logger.warning("这是警告日志")
    logger.error("这是错误日志")
    logger.critical("这是严重错误日志")


def structured_logging_example():
    """结构化日志示例"""
    print("\n=== 结构化日志示例 ===")

    # 绑定结构化数据
    user_logger = logger.bind(user_id=12345, username="john")
    user_logger.info("用户登录")
    user_logger.info("用户查看个人资料")

    # 绑定多个上下文
    request_logger = logger.bind(
        request_id="req-abc123",
        method="POST",
        path="/api/users"
    )
    request_logger.info("收到API请求")
    request_logger.success("请求处理成功")


def exception_logging_example():
    """异常日志示例"""
    print("\n=== 异常日志示例 ===")

    try:
        # 模拟一个错误
        result = 10 / 0
    except ZeroDivisionError:
        # 使用 exception() 自动记录堆栈信息
        logger.exception("计算过程中发生除零错误")


def context_logging_example():
    """上下文日志示例"""
    print("\n=== 上下文日志示例 ===")

    def process_order(order_id: int, user_id: int):
        """处理订单"""
        # 为整个函数绑定上下文
        order_logger = logger.bind(order_id=order_id, user_id=user_id)

        order_logger.info("开始处理订单")
        order_logger.debug("验证订单数据")
        order_logger.debug("计算订单总价")
        order_logger.success("订单处理完成")

    process_order(order_id=98765, user_id=12345)


def performance_logging_example():
    """性能日志示例"""
    print("\n=== 性能日志示例 ===")

    import time

    def slow_operation():
        """模拟耗时操作"""
        start = time.time()
        logger.info("开始执行耗时操作")

        # 模拟处理
        time.sleep(0.1)

        duration = time.time() - start
        logger.bind(duration=f"{duration:.3f}s").info("操作完成")

    slow_operation()


def filtered_logging_example():
    """过滤日志示例"""
    print("\n=== 过滤日志示例 ===")

    # 这些日志可能会被配置文件中的过滤器过滤掉
    logger.info("健康检查请求 /health")
    logger.info("指标收集 /metrics")
    logger.info("favicon请求 /favicon.ico")

    # 正常日志不会被过滤
    logger.info("用户API请求 /api/users")


if __name__ == "__main__":
    print("=" * 60)
    print("PySpring 日志系统使用示例")
    print("=" * 60)

    # 基础日志
    basic_logging_example()

    # 结构化日志
    structured_logging_example()

    # 异常日志
    exception_logging_example()

    # 上下文日志
    context_logging_example()

    # 性能日志
    performance_logging_example()

    # 过滤日志
    filtered_logging_example()

    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("=" * 60)
