"""
测试 GlobalExceptionHandler 是否正确注册为 IoC 组件
"""
import sys
from pathlib import Path

# 添加框架路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from pyspring.ioc.context import ApplicationContext
from pyspring.web.handlers.base import IExceptionHandler
from pyspring.web.handlers.exception import GlobalExceptionHandler

print("=" * 80)
print("🧪 测试异常处理器 IoC 注册")
print("=" * 80)

# 初始化容器
print("\n1️⃣ 初始化 ApplicationContext...")
context = ApplicationContext.initialize(
    config_file=None,  # 跳过配置文件，直接扫描框架包
    enable_aop=False
)

# 检查是否注册了 IExceptionHandler
print("\n2️⃣ 检查 IExceptionHandler 接口实现...")
try:
    handler = context.get_by_type(IExceptionHandler)
    print(f"✅ 找到异常处理器: {type(handler).__name__}")
    print(f"   类型: {handler.__class__.__module__}.{handler.__class__.__name__}")
    print(f"   是否为 GlobalExceptionHandler: {isinstance(handler, GlobalExceptionHandler)}")
except Exception as e:
    print(f"❌ 未找到异常处理器: {e}")
    sys.exit(1)

# 检查是否可以直接获取 GlobalExceptionHandler
print("\n3️⃣ 检查 GlobalExceptionHandler 单例...")
try:
    handler2 = context.get_by_type(GlobalExceptionHandler)
    print(f"✅ 找到 GlobalExceptionHandler")
    print(f"   单例验证: {handler is handler2} (应该为 True)")
except Exception as e:
    print(f"❌ 获取失败: {e}")

# 测试方法可用性
print("\n4️⃣ 测试方法可用性...")
methods = ['format_exception_info', 'log_exception', 'handle_http_exception',
           'handle_validation_exception', 'handle_general_exception',
           'register_exception_handlers']
for method in methods:
    has_method = hasattr(handler, method)
    print(f"   {'✅' if has_method else '❌'} {method}")

print("\n" + "=" * 80)
print("✅ 异常处理器 IoC 注册测试完成")
print("=" * 80)
