# PySpring CLI 命令行工具使用指南

## 📦 安装 PySpring CLI

### 推荐方式：使用 pipx 或 uv tool

```bash
# 方式 1: pipx（推荐）
pipx install pyspring

# 方式 2: uv tool（更快）
uv tool install pyspring

# 方式 3: 临时使用 uvx（无需安装）
uvx --from pyspring pyspring --help
```

### 为什么不推荐 pip install？

```bash
# ❌ 不推荐：全局安装会污染环境
pip install pyspring

# ✅ 推荐：使用 pipx 或 uv tool 隔离安装
pipx install pyspring
```

## 🎯 可用命令

### 1. init - 初始化项目

创建新的 PySpring 项目：

```bash
# 基本用法
pyspring init my-project

# 创建完整示例项目（推荐）
pyspring init my-project --example

# 创建最小配置项目
pyspring init my-project --minimal

# 强制覆盖已存在的文件
pyspring init my-project --force
```

**无需安装的方式**：

```bash
uvx --from pyspring pyspring init my-project --example
```

### 2. 其他命令（待添加）

```bash
# 查看版本
pyspring --version

# 查看帮助
pyspring --help

# 查看子命令帮助
pyspring init --help
```

## 🔄 CLI 升级

```bash
# pipx 升级
pipx upgrade pyspring

# uv tool 升级
uv tool upgrade pyspring

# pip 升级（如果你用的是 pip）
pip install --upgrade pyspring
```

## 🛠️ 使用场景

### 场景 1：首次创建项目

```bash
# 打开任意文件夹
cd D:\Projects

# 使用 uvx 临时运行（无需预安装）
uvx --from pyspring pyspring init my-first-app --example

# 进入项目
cd my-first-app

# 安装依赖并运行
uv sync
uv run uvicorn app.main:app --reload
```

### 场景 2：经常创建新项目

```bash
# 一次性安装 CLI 工具
pipx install pyspring

# 之后可以随时使用
cd D:\Projects
pyspring init project1 --example
pyspring init project2 --minimal
pyspring init project3
```

### 场景 3：CI/CD 环境

```yaml
# .github/workflows/test.yml
name: Test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install uv
        run: pip install uv
      
      - name: Create test project
        run: uvx --from pyspring pyspring init test-project --example
      
      - name: Test project
        run: |
          cd test-project
          uv sync
          uv run pytest tests/
```

### 场景 4：团队协作

**项目创建者**：

```bash
# 创建项目并推送到 Git
pyspring init team-project --example
cd team-project
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/team/project.git
git push -u origin main
```

**团队成员**：

```bash
# 克隆项目
git clone https://github.com/team/project.git
cd project

# 安装依赖（不需要安装 PySpring CLI）
uv sync

# 运行项目
uv run uvicorn app.main:app --reload
```

## 📝 命令参考

### pyspring init

```
用法: pyspring init [OPTIONS] [TARGET_DIR]

初始化 PySpring 项目结构

参数:
  TARGET_DIR              目标目录（默认：当前目录）

选项:
  -e, --example          创建完整示例项目（包含所有功能）
  -m, --minimal          创建最小配置项目
  -f, --force            强制覆盖已存在的文件
  --skip-env             跳过 .env 文件生成
  -h, --help             显示帮助信息
```

**示例**：

```bash
# 在当前目录初始化
pyspring init

# 在指定目录初始化
pyspring init /path/to/project

# 创建示例项目
pyspring init my-app --example

# 创建最小项目
pyspring init my-app --minimal

# 强制覆盖
pyspring init my-app --force --example
```

## 🔍 故障排除

### 问题 1：command not found: pyspring

**原因**：CLI 工具未安装或不在 PATH 中

**解决方案**：

```bash
# 检查是否安装
pipx list

# 如果未安装，重新安装
pipx install pyspring

# 确保 pipx 的 bin 目录在 PATH 中
pipx ensurepath
```

### 问题 2：想要最新版本

```bash
# 临时使用最新版本（无需更新本地安装）
uvx --from pyspring pyspring init --example

# 或者更新已安装的版本
pipx upgrade pyspring
```

### 问题 3：不同项目需要不同版本的 PySpring

**解决方案**：CLI 工具版本和项目依赖版本是分离的

```bash
# CLI 工具：用于创建项目
pipx install pyspring  # 可以是最新版

# 项目依赖：在 pyproject.toml 中指定
[project]
dependencies = [
    "pyspring==1.0.0",  # 项目锁定特定版本
]
```

## 💡 最佳实践

1. **使用 pipx 安装 CLI**：保持工具与项目依赖隔离
2. **使用 uvx 临时运行**：尝鲜或 CI/CD 环境
3. **定期更新 CLI**：`pipx upgrade pyspring`
4. **项目依赖独立管理**：在 `pyproject.toml` 中声明版本

## 📚 相关文档

- [安装指南](./INSTALLATION_GUIDE.md)
- [快速开始](./QUICK_REFERENCE.md)
- [示例项目指南](./EXAMPLE_PROJECT_GUIDE.md)
