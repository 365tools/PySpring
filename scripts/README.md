# PySpring Scripts 目录

此目录包含 PySpring 框架的构建、发布与开发辅助脚本。

## 发布脚本

### publish-individual.ps1 / publish-individual.sh

独立包发布脚本，用于按包发布 `pyspring` 和 `pyspring-cli`（适配 PEP 420 多包结构）。

#### 用法

PowerShell:
```powershell
# 发布 pyspring 聚合包到 TestPyPI
.\scripts\publish-individual.ps1 pyspring test

# 发布 pyspring-cli 到 TestPyPI
.\scripts\publish-individual.ps1 pyspring-cli test

# 发布到正式 PyPI
.\scripts\publish-individual.ps1 pyspring prod
```

Bash:
```bash
# 发布 pyspring 聚合包到 TestPyPI
./scripts/publish-individual.sh pyspring test

# 发布到正式 PyPI
./scripts/publish-individual.sh pyspring prod
```

#### 功能

1. **独立包发布**：可分别发布 `pyspring` 和 `pyspring-cli` 包
2. **版本检查**：自动从对应包的 `pyproject.toml` 读取版本号
3. **测试验证**：运行对应包的相关测试（`tests/` 目录）
4. **构建打包**：在包目录内构建分发包
5. **完整性检查**：`twine check` 验证构建的包
6. **目标选择**：支持发布到 TestPyPI 或正式 PyPI
7. **发布摘要**：生成发布摘要文件
8. **标签管理**：正式发布时创建 Git 标签

## 其他目录

- `db/` - 数据库初始化脚本（`init_sqlite.sql` / `init_postgresql.sql`）

## 使用建议

- 发布请统一使用 `publish-individual` 脚本
- 优先发布到 TestPyPI 验证，无误后再发布到正式 PyPI
