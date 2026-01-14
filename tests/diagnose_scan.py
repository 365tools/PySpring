"""
Diagnose why DBConnectionInitializer is not scanned
"""
import inspect
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pyspring.repositories.db.initializer.connection import DBConnectionInitializer
from pyspring.core.abstracts.interfaces.initializer.startup import IStartupInitializer
from pyspring.core.abstracts.interfaces.IService import IService

print(f"Class: {DBConnectionInitializer}")
print(f"Bases: {DBConnectionInitializer.__bases__}")
print(f"MRO: {DBConnectionInitializer.__mro__}")

print(f"Inherits IStartupInitializer? {issubclass(DBConnectionInitializer, IStartupInitializer)}")
print(f"Inherits IService? {issubclass(DBConnectionInitializer, IService)}")
print(f"Is abstract? {inspect.isabstract(DBConnectionInitializer)}")

if inspect.isabstract(DBConnectionInitializer):
    print("ABSTRACT METHODS:", DBConnectionInitializer.__abstractmethods__)

from pyspring.ioc.manager import AppContainerManager

manager = AppContainerManager()

# Simulate scan module logic
import pyspring.repositories.db.initializer.connection as module

print(f"\nScanning module: {module.__name__}")
print(f"Comparison: {DBConnectionInitializer.__module__} == {module.__name__} ? {DBConnectionInitializer.__module__ == module.__name__}")

is_service = False
try:
    if DBConnectionInitializer is not IService and issubclass(DBConnectionInitializer, IService):
        is_service = True
except TypeError:
    pass
print(f"Is Service Subclass? {is_service}")

# Try register
try:
    manager.register_service_by_convention(DBConnectionInitializer)
    print("Register successful")
except Exception as e:
    print(f"Register failed: {e}")
