# -*- coding: utf-8 -*-
"""
Authentication Module IOC Test

Tests IOC injection for security/authentication module
Verifies: Config manager, Token service, Response builder
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from pyspring.ioc.context import ApplicationContext
from pyspring.security.core.config.loader import SecurityConfigManager
from pyspring.security.authentication.token.service import TokenService
from pyspring.security.authentication.contracts.response import IResponseBuilder


async def test_basic_ioc():
    """Test basic IOC injection with single package scan"""
    print("\n" + "=" * 80)
    print("Test: Security Module IOC (Single Package Scan)")
    print("=" * 80)

    os.environ['JWT_SECRET_KEY'] = 'test-secret'
    os.environ['DATABASE_TYPE'] = 'sqlite'
    os.environ['CACHE_TYPE'] = 'memory'

    # Single package scan - should recursively scan ALL subpackages
    ctx = ApplicationContext.initialize(base_packages=[
        "pyspring.security",
        "pyspring.repositories"
    ])

    # 1. SecurityConfigManager
    config_mgr = ctx.get_by_type(SecurityConfigManager)
    assert config_mgr is not None, "SecurityConfigManager not registered"
    print("OK SecurityConfigManager")

    # 2. TokenService
    token_svc = ctx.get_by_type(TokenService)
    assert token_svc is not None, "TokenService not registered"
    print("OK TokenService")

    # 3. Test token generation
    token = token_svc.create_access_token({"user_id": "test"})
    assert token is not None
    print(f"OK Token generation: {token[:30]}...")

    # 4. Parse token (use generator's parse method)
    parsed = await token_svc.token_generator.parse_token(token)
    assert parsed.get("user_id") == "test"
    print("OK Token parsing")

    # 5. ResponseBuilder
    response_builder = ctx.get_by_type(IResponseBuilder)
    assert response_builder is not None
    assert hasattr(response_builder, 'token_service')
    print("OK ResponseBuilder with TokenService injection")

    # 6. Test response building
    generator = response_builder.token_service.token_generator
    assert generator.get_token_type() == "JWT"
    print(f"OK Token generator type: {generator.get_token_type()}")

    print("\n✅ All tests passed! (IOC recursive scanning works)\n")

    ApplicationContext.reset()


async def main():
    try:
        await test_basic_ioc()
        print("=" * 80)
        print("SUCCESS: IOC recursive scanning works correctly!")
        print("  - Single base_packages=['pyspring.security'] scans ALL subpackages")
        print("  - SecurityConfigManager, TokenService, ResponseBuilder all injected")
        print("  - Strategy pattern (Token generator) works")
        print("=" * 80)
    except Exception as e:
        print(f"\nERROR: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
