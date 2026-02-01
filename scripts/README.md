# PySpring Scripts 目录

此目录包含 PySpring 框架的各种脚本工具。

## 发布脚本

### publish-individual.ps1 / publish-individual.sh
独立发布脚本，用于分别发布 `pyspring` 和 `pyspring-cli` 包。

#### 用法

PowerShell:
```powershell
# 发布 pyspring 包到 TestPyPI
.\scripts\publish-individual.ps1 pyspring test

# 发布 pyspring-cli 包到 TestPyPI
.\scripts\publish-individual.ps1 pyspring-cli test

# 发布 pyspring 包到正式 PyPI
.\scripts\publish-individual.ps1 pyspring prod

# 发布 pyspring-cli 包到正式 PyPI
.\scripts\publish-individual.ps1 pyspring-cli prod
```

Bash:
```bash
# 发布 pyspring 包到 TestPyPI
./scripts/publish-individual.sh pyspring test

# 发布 pyspring-cli 包到 TestPyPI
./scripts/publish-individual.sh pyspring-cli test

# 发布 pyspring 包到正式 PyPI
./scripts/publish-individual.sh pyspring prod

# 发布 pyspring-cli 包到正式 PyPI
./scripts/publish-individual.sh pyspring-cli prod
```

#### 功能

1. **独立包发布**：可以分别发布 `pyspring` 和 `pyspring-cli` 包
2. **版本检查**：自动从对应包的 `pyproject.toml` 读取版本号
3. **测试验证**：运行对应包的相关测试
4. **构建打包**：在包目录内构建分发包
5. **完整性检查**：验证构建的包
6. **目标选择**：支持发布到 TestPyPI 或正式 PyPI
7. **发布摘要**：生成发布摘要文件
8. **标签管理**：正式发布时创建 Git 标签

## 现有脚本

### publish.ps1 / publish.sh
原有的统一发布脚本，用于发布整个项目。

### 其他脚本目录

- `db/` - 数据库相关脚本
- `development/` - 开发辅助脚本
- `diagnostics/` - 诊断和验证脚本
- `utilities/` - 实用工具脚本

## 使用建议

- 对于独立包的发布，请使用 `publish-individual` 脚本
- 对于整体项目发布，请使用原有的 `publish` 脚本
- 优先测试发布到 TestPyPI，验证无误后再发布到正式 PyPI