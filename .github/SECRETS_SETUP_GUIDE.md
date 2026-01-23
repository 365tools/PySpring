# GitHub Actions Secrets 配置指南

本文档说明如何配置 PySpring 自动发布所需的 GitHub Secrets。

## 📋 需要配置的 Secrets

| Secret 名称            | 用途           | 必需  | 获取方式                          |
|----------------------|--------------|-----|-------------------------------|
| `TESTPYPI_API_TOKEN` | 发布到 TestPyPI | ✅ 是 | [获取方法](#1-testpypi_api_token) |
| `PYPI_API_TOKEN`     | 发布到正式 PyPI   | ✅ 是 | [获取方法](#2-pypi_api_token)     |

---

## 🔐 配置步骤

### 步骤 1：获取 API Token

#### 1. TESTPYPI_API_TOKEN

TestPyPI 是测试环境，代码推送到 `main` 或 `develop` 分支时自动发布到这里。

**获取步骤**：

1. 访问 https://test.pypi.org/account/register/ 注册账号（如果还没有）
2. 验证邮箱
3. 访问 https://test.pypi.org/manage/account/token/
4. 点击 **"Add API token"**
5. 填写 Token 信息：
    - **Token name**: `PySpring GitHub Actions TestPyPI`
    - **Scope**: `Entire account (all projects)` （推荐）或选择 `pyspring` 项目
6. 点击 **"Add token"**
7. **⚠️ 重要**：立即复制生成的 token（格式：`pypi-AgEIcHl...`），只显示一次！

#### 2. PYPI_API_TOKEN

正式 PyPI 用于生产发布，创建 tag 时需要手动批准后才发布。

**获取步骤**：

1. 访问 https://pypi.org/account/register/ 注册账号（如果还没有）
2. 验证邮箱
3. **可选但推荐**：启用 2FA（两步验证）
4. 访问 https://pypi.org/manage/account/token/
5. 点击 **"Add API token"**
6. 填写 Token 信息：
    - **Token name**: `PySpring GitHub Actions PyPI`
    - **Scope**:
        - **首次发布前**：选择 `Entire account (all projects)`
        - **首次发布后**：可以创建项目专属 token，选择 `pyspring` 项目（更安全）
7. 点击 **"Add token"**
8. **⚠️ 重要**：立即复制生成的 token（格式：`pypi-AgEIcHl...`），只显示一次！

---

### 步骤 2：在 GitHub 配置 Secrets

#### 方式 1：通过 Web 界面配置（推荐）

1. 打开你的 GitHub 仓库：https://github.com/365tools/PySpring

2. 点击 **Settings** → **Secrets and variables** → **Actions**

3. 点击 **"New repository secret"**

4. 添加 `TESTPYPI_API_TOKEN`：
    - **Name**: `TESTPYPI_API_TOKEN`
    - **Value**: 粘贴之前复制的 TestPyPI token
    - 点击 **"Add secret"**

5. 重复步骤 3-4，添加 `PYPI_API_TOKEN`：
    - **Name**: `PYPI_API_TOKEN`
    - **Value**: 粘贴之前复制的 PyPI token
    - 点击 **"Add secret"**

#### 方式 2：通过 GitHub CLI 配置

```bash
# 安装 GitHub CLI（如果还没有）
# Windows: winget install GitHub.cli
# macOS: brew install gh
# Linux: https://github.com/cli/cli#installation

# 登录
gh auth login

# 设置 secrets
gh secret set TESTPYPI_API_TOKEN --body "pypi-AgEIcHl..."
gh secret set PYPI_API_TOKEN --body "pypi-AgEIcHl..."

# 验证
gh secret list
```

---

### 步骤 3：配置生产环境保护（Production Environment）

为了防止误发布到正式 PyPI，我们使用 GitHub Environment 保护机制。

**配置步骤**：

1. 在 GitHub 仓库中，点击 **Settings** → **Environments**

2. 点击 **"New environment"**

3. 创建环境：
    - **Name**: `production`
    - 点击 **"Configure environment"**

4. 配置保护规则：
    - ✅ 勾选 **"Required reviewers"**
    - 添加至少 1 个审核者（你自己或团队成员）
    - 可选：设置 **"Wait timer"**（例如 5 分钟冷静期）
    - 点击 **"Save protection rules"**

**完成后的效果**：

- 发布到 TestPyPI：推送代码后自动执行
- 发布到 PyPI：需要你在 GitHub Actions 页面点击 **"Review deployments"** 手动批准

---

## ✅ 验证配置

### 1. 检查 Secrets 是否配置成功

```bash
# 使用 GitHub CLI 检查
gh secret list

# 应该看到：
# TESTPYPI_API_TOKEN  Updated 2026-01-23
# PYPI_API_TOKEN      Updated 2026-01-23
```

或在 GitHub Web 界面：

- **Settings** → **Secrets and variables** → **Actions**
- 应该看到两个 secrets（值会被隐藏）

### 2. 测试 TestPyPI 自动发布

```bash
# 推送代码到 main 分支触发测试发布
git add .
git commit -m "test: trigger testpypi publish"
git push origin main

# 查看 Actions 执行情况
# https://github.com/365tools/PySpring/actions
```

**预期结果**：

- Actions 页面会显示 "Test - Publish to TestPyPI" workflow 正在运行
- 几分钟后完成，包会出现在 https://test.pypi.org/project/pyspring/

### 3. 测试 PyPI 生产发布

```bash
# 1. 更新版本号（如果需要）
# 编辑 pyproject.toml，修改 version = "1.0.1"

# 2. 提交并创建 tag
git add pyproject.toml
git commit -m "chore: bump version to 1.0.1"
git push

# 3. 创建并推送 tag
git tag v1.0.1
git push origin v1.0.1

# 4. 访问 Actions 页面
# https://github.com/365tools/PySpring/actions

# 5. 找到 "Production - Publish to PyPI" workflow

# 6. 点击 workflow，会看到等待审批状态

# 7. 点击 "Review deployments" → 选择 "production" → "Approve and deploy"
```

**预期结果**：

- 审批后，包会发布到正式 PyPI
- 自动创建 GitHub Release
- 用户可以通过 `uvx --from pyspring pyspring init` 使用

---

## 🔄 工作流程说明

### 测试环境发布（自动）

```
代码推送到 main/develop
         ↓
    运行测试
         ↓
    构建包
         ↓
   发布到 TestPyPI ✅
         ↓
   显示测试安装命令
```

**触发条件**：

- 推送到 `main` 或 `develop` 分支
- 不触发：仅修改 docs、markdown、workflow 文件

**适用场景**：

- 日常开发测试
- 功能验证
- 集成测试

### 生产环境发布（需批准）

```
创建 tag (v*.*.*)
         ↓
    运行测试
         ↓
    构建包
         ↓
   检查包质量
         ↓
  ⏸️ 等待手动批准 ⚠️
         ↓
   发布到 PyPI ✅
         ↓
   创建 GitHub Release
```

**触发条件**：

- 创建 `v*.*.*` 格式的 tag（如 `v1.0.0`）
- 或手动触发（需输入 "yes" 确认）

**手动批准步骤**：

1. 在 Actions 页面找到待审批的 workflow
2. 点击 "Review deployments"
3. 选择 "production" 环境
4. 点击 "Approve and deploy"

---

## 🚨 故障排除

### 问题 1：Secret 不存在

**错误信息**：

```
Error: Input required and not supplied: password
```

**解决方案**：

- 检查 Secret 名称是否完全匹配（区分大小写）
- 确认已经在 **Settings** → **Secrets and variables** → **Actions** 中添加

### 问题 2：Token 权限不足

**错误信息**：

```
403 Forbidden: Access was denied to this resource
```

**解决方案**：

- 检查 token 的 scope 是否包含目标项目
- 对于首次发布，需要使用 "Entire account" scope
- 首次发布后，可以创建项目专属 token

### 问题 3：版本号已存在

**错误信息**：

```
400 Bad Request: File already exists
```

**解决方案**：

- PyPI 不允许覆盖已发布的版本
- 需要在 `pyproject.toml` 中更新版本号
- 创建新的 tag

### 问题 4：Environment 保护未生效

**症状**：发布到 PyPI 没有等待批准

**解决方案**：

- 确认已创建 `production` environment（注意名称完全匹配）
- 确认已在 environment 中添加 Required reviewers
- 检查 workflow 文件中的 `environment: name: production` 配置

---

## 📝 最佳实践

### 1. Token 安全

- ✅ **永远不要**在代码中硬编码 token
- ✅ **永远不要**在公开的地方分享 token
- ✅ Token 只显示一次，立即保存到安全的地方
- ✅ 定期轮换 token（建议每 6-12 个月）
- ✅ 给 token 起有意义的名称，方便管理

### 2. 发布流程

- ✅ **先测试后生产**：推送到 main → 在 TestPyPI 测试 → 确认无误后打 tag → 发布生产
- ✅ **版本号管理**：遵循语义化版本（SemVer）
- ✅ **更新 CHANGELOG**：每次发布前更新变更日志
- ✅ **测试充分**：生产发布不可逆，确保充分测试

### 3. Tag 命名规范

```bash
# ✅ 正确格式
v1.0.0
v2.1.3
v0.1.0-beta

# ❌ 错误格式（不会触发生产发布）
1.0.0
version-1.0.0
release-v1.0.0
```

---

## 🔗 相关资源

- [TestPyPI 文档](https://test.pypi.org/help/)
- [PyPI 文档](https://pypi.org/help/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [GitHub Environments 文档](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Twine 文档](https://twine.readthedocs.io/)

---

## ✅ 配置检查清单

在开始自动发布前，确认以下项目：

- [ ] 已注册 TestPyPI 账号并验证邮箱
- [ ] 已注册 PyPI 账号并验证邮箱
- [ ] 已创建 TestPyPI API token
- [ ] 已创建 PyPI API token
- [ ] 已在 GitHub 配置 `TESTPYPI_API_TOKEN` secret
- [ ] 已在 GitHub 配置 `PYPI_API_TOKEN` secret
- [ ] 已创建 `production` environment
- [ ] 已在 `production` environment 配置 Required reviewers
- [ ] 已测试 TestPyPI 自动发布（推送到 main）
- [ ] 已测试 PyPI 手动批准流程（创建 tag）

**全部完成后，你的自动发布流程就配置好了！** 🎉
