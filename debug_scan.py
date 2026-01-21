import logging
import sys

from pyspring.ioc.manager import AppContainerManager

from pyspring.security.authorization.contracts.permission import IPermissionService

# Configure logging to stdout
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

# Force register
manager = AppContainerManager()
# Add specific package to config manually if needed, but it should be in FRAMEWORK_PACKAGES
print(f"Framework packages: {manager.FRAMEWORK_PACKAGES}")

# Run scan
manager.register_all_services()

print("Scanning completed")

# Check IPermissionService mapping
impl = manager._interface_impl_map.get(IPermissionService)
print(f"IPermissionService map: {impl}")

# Check binding
name = manager.generate_name(IPermissionService)
print(f"IPermissionService name: {name}")

binding_exists = manager.container.has_binding("default_permission_service")
print(f"default_permission_service binding exists: {binding_exists}")

try:
    svc = manager.service(IPermissionService)
    print(f"Got IPermissionService: {svc}")
except Exception as e:
    print(f"Failed to get IPermissionService: {e}")
