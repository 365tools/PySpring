from unittest.mock import MagicMock
from fastapi import Request

# 创建mock
request = MagicMock(spec=Request)
request.__class__ = Request
request.state = MagicMock()
request.state.user_id = "user123"

print(f"type(request): {type(request)}")
print(f"request.__class__: {request.__class__}")
print(f"isinstance(request, Request): {isinstance(request, Request)}")
print(f"hasattr(request, 'state'): {hasattr(request, 'state')}")

# 模拟装饰器中的检查
for arg in (request,):
    print(f"\nChecking arg: {arg}")
    print(f"  isinstance(arg, Request): {isinstance(arg, Request)}")
    print(f"  hasattr(arg, 'state'): {hasattr(arg, 'state')}")
    print(f"  hasattr(arg, '__class__'): {hasattr(arg, '__class__')}")
    if isinstance(arg, Request) or (hasattr(arg, 'state') and hasattr(arg, '__class__')):
        print("  ✓ MATCHED!")
    else:
        print("  ✗ NOT MATCHED!")
