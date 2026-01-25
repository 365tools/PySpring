"""
诊断 py-demo 项目中的问题
"""
import os
import sys

# 添加项目路径
project_path = r"D:\Project\PycharmProjects\py-demo"
if os.path.exists(project_path):
    sys.path.insert(0, project_path)

print("=" * 60)
print("诊断 py-demo 项目问题")
print("=" * 60)
print()

# 检查1：文件是否存在
print("检查1：检查关键文件...")
security_config_path = os.path.join(project_path, "app", "config", "security_config.py")
if os.path.exists(security_config_path):
    print(f"✅ security_config.py 存在")
    print(f"   路径: {security_config_path}")

    # 读取文件内容
    print("\n文件内容（前80行）：")
    print("-" * 60)
    with open(security_config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:80], 1):
            print(f"{i:3d}: {line.rstrip()}")
    print("-" * 60)
else:
    print(f"❌ security_config.py 不存在")
    print(f"   期望路径: {security_config_path}")

print()

# 检查2：Python 版本
print("检查2：Python 版本...")
print(f"✅ Python 版本: {sys.version}")
print()

# 检查3：尝试导入框架的 SecurityEntityConfiguration
print("检查3：导入框架的 SecurityEntityConfiguration...")
try:
    from pyspring.security.authentication.config.entity import SecurityEntityConfiguration

    print(f"✅ 成功导入 SecurityEntityConfiguration")
    print(f"   类型: {type(SecurityEntityConfiguration)}")
    print(f"   是否是类: {isinstance(SecurityEntityConfiguration, type)}")
    print(f"   模块: {SecurityEntityConfiguration.__module__}")

    # 检查装饰器
    print(f"   装饰器标记:")
    print(f"     __pyspring_component__: {hasattr(SecurityEntityConfiguration, '__pyspring_component__')}")
    print(f"     __pyspring_conditional__: {hasattr(SecurityEntityConfiguration, '__pyspring_conditional__')}")

except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback

    traceback.print_exc()

print()

# 检查4：尝试导入用户的模型
print("检查4：尝试导入用户的 User 模型...")
try:
    # 先不导入 security_config，只导入 User
    if os.path.exists(os.path.join(project_path, "app", "config", "security_config.py")):
        # 读取文件，查找 User 的导入
        with open(security_config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'from app.models' in content:
                print("   发现导入: from app.models")
            if 'import User' in content:
                print("   发现导入: import User")

        # 尝试直接导入 User
        try:
            from app.models import User

            print(f"✅ 成功导入 User")
            print(f"   类型: {type(User)}")
            print(f"   是否是类: {isinstance(User, type)}")
        except Exception as e:
            print(f"❌ 导入 User 失败: {e}")
            import traceback

            traceback.print_exc()
except Exception as e:
    print(f"❌ 检查失败: {e}")

print()

# 检查5：查找 __pycache__ 文件
print("检查5：查找 Python 缓存文件...")
pycache_count = 0
for root, dirs, files in os.walk(project_path):
    if '__pycache__' in dirs:
        pycache_count += 1
        print(f"   发现缓存: {root}")

if pycache_count > 0:
    print(f"⚠️  发现 {pycache_count} 个 __pycache__ 目录")
    print("   建议清理缓存文件")
else:
    print("✅ 未发现缓存文件")

print()
print("=" * 60)
print("诊断完成")
print("=" * 60)
