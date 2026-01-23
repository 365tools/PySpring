# PySpring 发布到 PyPI 指南

## 📦 为什么要发布到 PyPI？

当你发布 PySpring 到 PyPI 后，用户就可以：

```bash
# 直接临时运行（无需预安装）
uvx --from pyspring pyspring init my-project --example

# 或安装 CLI 工具
pipx install pyspring

# 或在项目中使用
pip install pyspring
uv add pyspring
```

**不发布到 PyPI 的话**，用户只能通过以下方式安装：

- 从 GitHub 克隆源码手动安装
- 从本地路径安装：`pip install /path/to/pyspring`
- 从 Git 安装：`pip install git+https://github.com/365tools/PySpring.git`

## ✅ 发布前检查清单

### 1. 检查 pyproject.toml 配置

```toml
[project]
name = "pyspring"                    # ✅ 包名（PyPI 唯一）
version = "1.0.0"                    # ✅ 版本号
description = "..."                  # ✅ 简短描述
readme = "README.md"                 # ✅ 详细说明
requires-python = ">=3.12"           # ✅ Python 版本要求
license = {text = "Apache-2.0"}      # ✅ 许可证

[project.urls]
"Homepage" = "https://github.com/365tools/PySpring"  # ✅ 项目主页
"Documentation" = "https://..."      # 📝 文档地址
"Bug Tracker" = "https://..."        # ✅ 问题跟踪

[project.scripts]
pyspring = "pyspring.cli.main:main"  # ✅ CLI 命令入口

[tool.setuptools.package-data]
pyspring = [
    "templates/**/*",                # ✅ 包含模板文件
]
```

### 2. 确保包含所有必要文件

```bash
PySpring/
├── src/pyspring/              # ✅ 源代码
├── pyproject.toml             # ✅ 项目配置
├── README.md                  # ✅ 说明文档
├── LICENSE                    # ✅ 许可证文件
├── CHANGELOG.md               # 📝 更新日志（推荐）
└── MANIFEST.in               # 📝 额外文件（如需要）
```

### 3. 测试本地构建

```bash
# 安装构建工具
pip install build twine

# 构建包
python -m build

# 检查生成的文件
ls dist/
# 应该看到：
# pyspring-1.0.0-py3-none-any.whl
# pyspring-1.0.0.tar.gz

# 检查包的完整性
twine check dist/*
```

### 4. 测试本地安装

```bash
# 在虚拟环境中测试安装
python -m venv test-env
test-env\Scripts\activate  # Windows
# source test-env/bin/activate  # macOS/Linux

# 从本地 wheel 安装
pip install dist/pyspring-1.0.0-py3-none-any.whl

# 测试 CLI 命令
pyspring --version
pyspring init test-project --example

# 清理
deactivate
rm -rf test-env test-project
```

## 🚀 发布流程

### 方式 1：使用 TestPyPI 测试（推荐先测试）

TestPyPI 是 PyPI 的测试服务器，可以安全测试发布流程。

#### 步骤 1：注册账号

1. 访问 https://test.pypi.org/account/register/
2. 注册账号并验证邮箱
3. 创建 API Token：https://test.pypi.org/manage/account/token/

#### 步骤 2：配置凭据

```bash
# 方式 A：使用 .pypirc 文件
cat > ~/.pypirc << EOF
[distutils]
index-servers =
    pypi
    testpypi

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHl...  # 你的 TestPyPI token

[pypi]
repository = https://upload.pypi.org/legacy/
username = __token__
password = pypi-AgEIcHl...  # 你的 PyPI token（稍后添加）
EOF

# Windows PowerShell:
# 在 C:\Users\YourName\.pypirc 创建上述文件
```

#### 步骤 3：上传到 TestPyPI

```bash
# 清理旧的构建
rm -rf dist/ build/ *.egg-info

# 构建包
python -m build

# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 或者直接指定
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

#### 步骤 4：从 TestPyPI 测试安装

```bash
# 创建新的虚拟环境测试
python -m venv test-testpypi
test-testpypi\Scripts\activate

# 从 TestPyPI 安装（需要指定额外的索引因为依赖在正式 PyPI）
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyspring

# 测试功能
pyspring --version
pyspring init test-project --example

# 测试 uvx
uvx --from pyspring --index-url https://test.pypi.org/simple/ pyspring init test2 --example
```

### 方式 2：发布到正式 PyPI

**⚠️ 注意**：发布到正式 PyPI 后无法删除版本号，请确保测试无误！

#### 步骤 1：注册正式 PyPI 账号

1. 访问 https://pypi.org/account/register/
2. 注册账号并验证邮箱
3. 创建 API Token：https://pypi.org/manage/account/token/
4. 更新 `~/.pypirc` 添加正式 PyPI token

#### 步骤 2：发布

```bash
# 确保已经在 TestPyPI 测试过！

# 清理并重新构建
rm -rf dist/ build/ *.egg-info
python -m build

# 最后检查
twine check dist/*

# 上传到 PyPI（需要确认）
twine upload dist/*

# 上传时会提示输入：
# Enter your username: __token__
# Enter your password: <你的 PyPI token>
```

#### 步骤 3：验证发布

```bash
# 等待几分钟让 PyPI 索引更新

# 访问包页面
# https://pypi.org/project/pyspring/

# 测试安装
pip install pyspring

# 测试 uvx
uvx --from pyspring pyspring init my-project --example

# 测试 pipx
pipx install pyspring
pyspring --version
```

## 🔄 版本更新发布

### 1. 更新版本号

```toml
# pyproject.toml
[project]
version = "1.0.1"  # 或 1.1.0, 2.0.0 等
```

### 2. 更新 CHANGELOG

```markdown
# CHANGELOG.md

## [1.0.1] - 2026-01-23

### Added
- 新增 --example 参数创建完整示例项目

### Fixed
- 修复模板文件复制问题

### Changed
- 更新文档说明
```

### 3. 提交并打标签

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main --tags
```

### 4. 重新构建和发布

```bash
rm -rf dist/ build/ *.egg-info
python -m build
twine check dist/*
twine upload dist/*
```

## 🤖 使用 GitHub Actions 自动发布

创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # 用于 trusted publishing
      
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: twine check dist/*
    
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}
```

### 配置 GitHub Secrets

1. 访问 GitHub 仓库 Settings → Secrets and variables → Actions
2. 添加 secret：`PYPI_API_TOKEN`（值为你的 PyPI API token）

### 使用方式

```bash
# 1. 更新版本号并提交
# 2. 在 GitHub 创建 Release
# 3. GitHub Actions 自动构建并发布到 PyPI
```

## 📋 发布后用户使用方式

发布成功后，用户可以通过以下方式使用：

### 1. 临时运行（推荐给新用户）

```bash
uvx --from pyspring pyspring init my-project --example
```

### 2. 安装 CLI 工具（推荐给开发者）

```bash
pipx install pyspring
pyspring init my-project --example
```

### 3. 项目依赖

```bash
# 在项目中使用
pip install pyspring

# 或使用 uv
uv add pyspring
```

## 🔍 故障排除

### 问题 1：包名已被占用

```
ERROR: The name 'pyspring' is already taken
```

**解决方案**：

- 检查 https://pypi.org/project/pyspring/ 是否已存在
- 如果是你的包，使用相同账号发布新版本
- 如果被占用，考虑改名：`pyspring-framework`, `pyspring-ioc` 等

### 问题 2：模板文件未包含在包中

用户安装后运行 `pyspring init` 报错找不到模板。

**解决方案**：确保 `pyproject.toml` 正确配置：

```toml
[tool.setuptools.package-data]
pyspring = [
    "templates/**/*",
    "templates/**/*.template",
]
```

测试：

```bash
python -m build
unzip -l dist/pyspring-1.0.0-py3-none-any.whl | grep templates
# 应该看到所有模板文件
```

### 问题 3：依赖版本冲突

**解决方案**：使用合理的版本范围

```toml
dependencies = [
    "fastapi>=0.104.0,<1.0.0",     # 指定范围
    "sqlalchemy>=2.0.0,<3.0.0",
]
```

## 📚 相关资源

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI 官方文档](https://pypi.org/help/)
- [Twine 文档](https://twine.readthedocs.io/)
- [setuptools 文档](https://setuptools.pypa.io/)
- [GitHub Actions PyPI Publish](https://github.com/marketplace/actions/pypi-publish)

## 🎯 推荐的发布流程

```bash
# === 开发阶段 ===
# 1. 本地开发测试
pip install -e .
pyspring init test --example

# === 准备发布 ===
# 2. 更新版本号和 CHANGELOG
# 3. 提交代码
git add .
git commit -m "Prepare for release v1.0.0"

# === 测试发布 ===
# 4. 先发布到 TestPyPI 测试
python -m build
twine upload --repository testpypi dist/*

# 5. 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyspring

# === 正式发布 ===
# 6. 确认无误后发布到正式 PyPI
rm -rf dist/
python -m build
twine upload dist/*

# 7. 打标签
git tag v1.0.0
git push origin v1.0.0

# === 验证 ===
# 8. 等待几分钟，然后测试
uvx --from pyspring pyspring init my-app --example
```

---

**记住**：发布到 PyPI 是不可逆的（版本号不能删除），所以：

1. ✅ 始终先在 TestPyPI 测试
2. ✅ 仔细检查版本号
3. ✅ 确保所有文件都包含在包中
4. ✅ 测试安装和功能正常
