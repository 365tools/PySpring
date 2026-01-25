"""
检查 ORM 模型是否正确注册
"""
from pyspring.repositories.db.models.common.define import Base

print("=" * 60)
print("🔍 检查 ORM 模型注册")
print("=" * 60)

print(f"\n📊 Base.metadata 中注册的表 ({len(Base.metadata.tables)} 个):")
for table_name in sorted(Base.metadata.tables.keys()):
    table = Base.metadata.tables[table_name]
    print(f"\n  表名: {table_name}")
    print(f"  列:")
    for column in table.columns:
        print(f"    - {column.name}: {column.type}")

print("\n" + "=" * 60)
print(f"✅ 总计 {len(Base.metadata.tables)} 个表已注册")
print("=" * 60)
