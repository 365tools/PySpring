# PySpring 使用指南

## 安装

### 开发环境安装

使用 uv 安装开发环境（推荐）：

```bash
# 确保已在项目根目录
uv sync --dev
```

### 命令行工具使用

安装后，您可以使用以下命令：

```bash
# 查看所有可用命令
pyspring --help

# 初始化新项目
pyspring init my-project

# 检查项目健康状况
pyspring check imports-circular  # 检查循环依赖
pyspring check diagnose        # 诊断环境问题

# 清理项目
pyspring clean cache          # 清理缓存
pyspring clean imports-reset  # 重置导入

# 项目初始化和同步
pyspring setup               # 设置项目环境
pyspring uv setup           # 设置 UV 环境
```

### 作为库使用

如果您想在代码中使用 PySpring 框架：

```python
import pyspring
# 使用框架功能
```

## 项目结构

```
packages/
├── pyspring/          # 核心框架项目
│   └── src/
│       └── pyspring/  # 框架源代码
└── pyspring-cli/      # 命令行工具项目
    └── src/
        └── pyspring_cli/ # CLI源代码
```

## 依赖管理

- 使用 `uv` 进行依赖管理
- 工作区成员定义在根目录的 `pyproject.toml` 中
- 依赖锁定文件为 `uv.lock`
- 只需运行 `uv sync --dev` 即可安装所有依赖