import os
import sys

# Add src to sys.path if not present (mimicking project setup)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from pyspring.security.base.config.loader import SecurityConfigManager
from pyspring.log.instance import logger

print("First instantiation:")
s1 = SecurityConfigManager()
print(f"S1 ID: {id(s1)}")

print("\nSecond instantiation:")
s2 = SecurityConfigManager()
print(f"S2 ID: {id(s1)}")

print(f"\nIs same instance? {s1 is s2}")

print("\nChecking _config:")
print(f"S1 config loaded: {s1._config is not None}")

# Check imports
import pyspring.security.base.config.loader as m1

print(f"\nModule 1: {m1}")

try:
    import src.pyspring.security.base.config.loader as m2

    print(f"Module 2: {m2}")
    print(f"Modules equal? {m1 == m2}")

    print("Instance from m2:")
    s3 = m2.SecurityConfigManager()
    print(f"S3 ID: {id(s3)}")
    print(f"S1 is S3? {s1 is s3}")

except ImportError:
    print("Could not import via src.pyspring...")
