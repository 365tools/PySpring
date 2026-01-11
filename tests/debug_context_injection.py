from pyspring.ioc.manager import AppContainerManager
from pyspring.log.instance import logger
from pyspring.security.authentication.impl.core.context import SecurityContextManager

print("🔍 检查 SecurityContextManager 注册情况")

manager = AppContainerManager()
# 强制扫描
manager.scan_and_register_services("pyspring.security")

# 检查服务名
expected_name = manager.generate_name(SecurityContextManager)
print(f"预期服务名: {expected_name}")

if expected_name in manager._registered_services:
    print(f"✅ 服务 {expected_name} 已注册")
    instance = manager.get(SecurityContextManager)
    print(f"✅ 获取实例成功: {instance}")
else:
    print(f"❌ 服务 {expected_name} 未被注册")
    print(f"当前已注册服务: {manager._registered_services}")

# 检查 LoginService 的依赖解析
from pyspring.security.authentication.impl.session.login import LoginService

print("\n🔍 模拟注册 LoginService")
try:
    manager.register_service(LoginService)
    login_service = manager.get(LoginService)
    print("✅ LoginService 获取成功")
except Exception as e:
    print(f"❌ LoginService 获取失败: {e}")
