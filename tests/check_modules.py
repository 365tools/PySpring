import os
import sys

# Add src to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from pyspring.security.base.config.loader import SecurityConfigManager

s = SecurityConfigManager()

print("\nloaded modules ending in loader:")
for name, mod in sys.modules.items():
    if 'loader' in name and 'security' in name:
        print(f"{name}: {mod}")
        if hasattr(mod, 'SecurityConfigManager'):
            cls = mod.SecurityConfigManager
            print(f"  Class ID: {id(cls)}")
            print(f"  Instance: {cls._instance}")
