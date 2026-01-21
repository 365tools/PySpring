import sys

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    from pyspring.repositories.db.config import DatabaseConfig, PostgreSQLConfig

    print("Imported DatabaseConfig")
    try:
        cfg = PostgreSQLConfig()
        print(f"PostgreSQLConfig init success: {cfg}")
    except Exception as e:
        print(f"PostgreSQLConfig init failed: {e}")
        import traceback

        traceback.print_exc()

except Exception as e:
    print(f"Import failed: {e}")

print("-" * 20)
print("Testing asyncpg import...")
try:
    import asyncpg

    print(f"asyncpg imported successfully: {asyncpg.__version__}")
    from asyncpg.protocol import protocol

    print("asyncpg.protocol.protocol imported")
    print(f"Protocol: {protocol.Protocol}")
except ImportError as e:
    print(f"asyncpg import failed: {e}")
except Exception as e:
    print(f"asyncpg other error: {e}")
