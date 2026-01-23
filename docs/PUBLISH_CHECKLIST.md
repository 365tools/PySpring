# PySpring 快速发布检查清单

## 📋 发布前最后检查（5 分钟）

### ✅ 第 1 步：版本和文档

- [ ] `pyproject.toml` 中更新版本号
- [ ] `CHANGELOG.md` 记录本次更新内容
- [ ] `README.md` 内容准确且完整
- [ ] 许可证文件存在

### ✅ 第 2 步：代码质量

- [ ] 运行所有测试：`pytest tests/`
- [ ] 代码无明显错误
- [ ] CLI 命令本地可用：`python -m pyspring.cli.main --version`

### ✅ 第 3 步：构建检查

```bash
# 清理旧构建
rm -rf dist/ build/ *.egg-info

# 构建
python -m build

# 检查
twine check dist/*

# 验证包内容
unzip -l dist/pyspring-*.whl | grep templates
# 必须看到 templates/example/ 下的所有文件！
```

### ✅ 第 4 步：本地测试安装

```bash
# 创建测试环境
python -m venv test-env
test-env\Scripts\activate

# 本地安装
pip install dist/pyspring-*.whl

# 测试 CLI
pyspring --version
pyspring init test-project --example
cd test-project
ls  # 检查文件是否完整

# 清理
cd ..
deactivate
rm -rf test-env test-project
```

### ✅ 第 5 步：TestPyPI 测试（强烈推荐）

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 等待 1-2 分钟

# 从 TestPyPI 安装测试
python -m venv test-testpypi
test-testpypi\Scripts\activate
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyspring

# 测试功能
pyspring init test --example
```

### ✅ 第 6 步：正式发布

```bash
# ⚠️ 确认以上都通过后才执行！

# 清理并重新构建（确保干净）
rm -rf dist/ build/ *.egg-info
python -m build
twine check dist/*

# 上传到 PyPI
twine upload dist/*

# Git 标签
git tag v1.0.0
git push origin v1.0.0
```

### ✅ 第 7 步：发布验证

```bash
# 等待 5-10 分钟让 PyPI 索引

# 验证包页面
# 访问：https://pypi.org/project/pyspring/

# 测试安装
pip install pyspring

# 测试 uvx（最重要！）
uvx --from pyspring pyspring init my-app --example
cd my-app
cat README.md  # 检查
```

## 🚨 常见错误检查

- [ ] ❌ 版本号忘记更新 → ✅ 检查 `pyproject.toml`
- [ ] ❌ 模板文件未包含 → ✅ 检查 wheel 内容
- [ ] ❌ 依赖版本过严 → ✅ 使用版本范围 `>=x.x.x,<y.0.0`
- [ ] ❌ README 中的链接失效 → ✅ 测试所有链接
- [ ] ❌ CLI 入口点错误 → ✅ 本地测试命令

## ⏱️ 首次发布估计时间

- 准备和检查：15 分钟
- TestPyPI 测试：10 分钟
- 正式发布：5 分钟
- 发布验证：10 分钟
- **总计：约 40 分钟**

## 🔄 后续版本发布

- 小版本更新（bugfix）：10 分钟
- 中版本更新（feature）：20 分钟
- 大版本更新（breaking）：40 分钟

---

**保存这个检查清单**，每次发布前过一遍！
