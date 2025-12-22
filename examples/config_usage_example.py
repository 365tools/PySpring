"""
配置使用示例 - 演示配置重载和点号路径访问

展示 SystemService 的三种配置访问方式：
1. 直接属性访问（推荐）
2. 点号路径访问（新增 get_config）
3. 配置重载
"""
from pyspring.system.impl.service import SystemService


def example_direct_access():
    """方式1: 直接属性访问（类型安全，IDE 智能提示）"""
    print("\n=== 方式1: 直接属性访问 ===")

    service = SystemService()

    # 访问服务器配置
    host = service.settings.app.server.host
    port = service.settings.app.server.port
    debug = service.settings.app.server.debug

    print(f"服务器: {host}:{port}")
    print(f"调试模式: {debug}")

    # 访问数据库配置
    db_host = service.settings.database.postgresql.host
    db_name = service.settings.database.postgresql.database

    print(f"数据库: {db_host}/{db_name}")

    # 访问 Redis 配置
    redis_host = service.settings.redis.host
    redis_port = service.settings.redis.port

    print(f"Redis: {redis_host}:{redis_port}")

    # 访问认证配置
    jwt_algo = service.settings.authentication.jwt.algorithm
    jwt_expire = service.settings.authentication.jwt.access_token_expire_minutes

    print(f"JWT: {jwt_algo}, 过期时间: {jwt_expire}分钟")


def example_dot_notation_yaml():
    """方式2: 点号路径访问 YAML 文件（灵活，支持任意配置文件）"""
    print("\n=== 方式2: 点号路径访问 YAML ===")

    service = SystemService()

    # 从 application.yaml 读取
    host = service.get_config("server.host", "0.0.0.0")
    port = service.get_config("server.port", 8000)
    app_name = service.get_config("app.name", "PySpring")

    print(f"应用: {app_name}")
    print(f"服务器: {host}:{port}")

    # 读取嵌套配置
    health_path = service.get_config("monitoring.health_check.path", "/health")
    metrics_enabled = service.get_config("monitoring.metrics.enabled", False)

    print(f"健康检查: {health_path}")
    print(f"监控指标: {metrics_enabled}")

    # 从其他配置文件读取
    log_level = service.get_config("level", "INFO", config_file="logging.yaml")
    cors_enabled = service.get_config("cors.enabled", False, config_file="security.yaml")

    print(f"日志级别: {log_level}")
    print(f"CORS 启用: {cors_enabled}")


def example_backward_compatible():
    """方式3: get() 方法访问配置"""
    print("\n=== 方式3: get() 方法 ===")

    service = SystemService()

    # 获取服务器配置对象
    server_config = service.get("server")
    if server_config:
        print(f"服务器配置: {server_config.host}:{server_config.port}")

    # 获取数据库配置对象
    database_config = service.get("database")
    if database_config:
        print(f"数据库类型: {database_config.type}")

    # 获取认证配置
    auth_config = service.get("authentication")
    if auth_config:
        print(f"JWT算法: {auth_config.jwt.algorithm}")


def example_reload():
    """配置重载示例"""
    print("\n=== 配置重载 ===")

    service = SystemService()

    # 读取初始配置
    print("初始配置:")
    host = service.get_config("server.host", "0.0.0.0")
    print(f"  Host: {host}")

    # 模拟配置文件被修改...
    print("\n假设 application.yaml 已被修改...")

    # 重新加载配置（清除缓存）
    success = service.reload()
    print(f"重载结果: {'成功' if success else '失败'}")

    # 读取新配置
    print("\n重载后配置:")
    host = service.get_config("server.host", "0.0.0.0")
    print(f"  Host: {host}")

    print("\n注意: reload() 主要清除缓存，完整重载需要重启应用")


def example_runtime_update():
    """运行时配置更新"""
    print("\n=== 运行时配置更新 ===")

    service = SystemService()

    # 读取原始值
    original_port = service.settings.app.server.port
    print(f"原始端口: {original_port}")

    # 动态修改配置
    success = service.set("app.server.port", 9000)
    print(f"修改结果: {'成功' if success else '失败'}")

    # 验证修改
    new_port = service.settings.app.server.port
    print(f"新端口: {new_port}")

    print("\n注意: 动态修改只在当前进程有效，不会持久化")


def example_validation():
    """配置验证"""
    print("\n=== 配置验证 ===")

    service = SystemService()

    # 验证配置完整性
    is_valid = service.validate()
    print(f"配置验证: {'通过' if is_valid else '失败'}")

    # Pydantic 会自动验证类型
    try:
        # 尝试设置错误类型
        service.set("app.server.port", "invalid")  # 应该是整数
    except Exception as e:
        print(f"类型验证错误: {e}")


def example_environment_variables():
    """环境变量覆盖配置"""
    print("\n=== 环境变量覆盖 ===")

    import os

    # 设置环境变量（优先级最高）
    os.environ["APP__SERVER__PORT"] = "9999"

    # 重新创建 service 以加载环境变量
    # 注意: 环境变量使用 __ 作为分隔符
    print("设置环境变量: APP__SERVER__PORT=9999")
    print("重启应用后，配置将从环境变量读取")
    print("配置优先级: 环境变量 > .env 文件 > YAML 文件 > 默认值")


if __name__ == "__main__":
    print("=" * 60)
    print("PySpring 配置使用示例")
    print("=" * 60)

    # 方式1: 推荐用法（类型安全）
    example_direct_access()

    # 方式2: 灵活访问 YAML
    example_dot_notation_yaml()

    # 方式3: 向后兼容
    example_backward_compatible()

    # 配置重载
    example_reload()

    # 运行时更新
    example_runtime_update()

    # 配置验证
    example_validation()

    # 环境变量
    example_environment_variables()

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)
