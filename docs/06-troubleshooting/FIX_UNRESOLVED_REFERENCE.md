# 解决 IDE "Unresolved reference 'pyspring'" 问题

## 问题描述

虽然 `pyspring diagnose` 显示一切正常，但 IDE（VS Code/PyCharm）仍然提示：

```
Unresolved reference 'pyspring'
```

## 根本原因

你在**全局 Python 环境**中安装了 PySpring，但：

- IDE 可能配置使用了虚拟环境
- 或 IDE 没有索引到全局环境
- IDE 无法找到全局安装的包

## ✅ 正确的解决方案

### 步骤 1: 在项目中创建虚拟环境

```powershell
# 进入你的项目目录
cd D:\Project\PycharmProjects\FastAPIProject

# 创建虚拟环境
python -m venv venv
```

### 步骤 2: 激活虚拟环境

```powershell
# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows CMD
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

激活后，命令提示符前会显示 `(venv)`：

```
(venv) PS D:\Project\PycharmProjects\FastAPIProject>
```

### 步骤 3: 在虚拟环境中安装 PySpring

```powershell
# 从 PyPI 安装（生产环境）
pip install pyspring

# 或从本地源码安装（开发模式）
pip install -e D:\Project\PycharmProjects\PySpring
```

### 步骤 4: 验证安装

```powershell
# 再次运行诊断
pyspring diagnose

# 现在应该显示：是否在虚拟环境: ✅ 是
```

### 步骤 5: 配置 IDE

#### 🟦 VS Code

**5.1 选择 Python 解释器**

```
1. 按 Ctrl+Shift+P
2. 输入并选择: "Python: Select Interpreter"
3. 选择: .\venv\Scripts\python.exe
```

**5.2 重启语言服务器**

```
1. 按 Ctrl+Shift+P
2. 输入并选择: "Python: Restart Language Server"
```

**5.3 重新加载窗口**

```
1. 按 Ctrl+Shift+P
2. 输入并选择: "Developer: Reload Window"
```

**5.4 配置 settings.json（可选）**

在项目根目录创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true,
    "python.analysis.extraPaths": [],
    "python.languageServer": "Pylance"
}
```

#### 🟧 PyCharm

**5.1 设置项目解释器**

```
1. File → Settings (或 Ctrl+Alt+S)
2. Project: FastAPIProject → Python Interpreter
3. 点击齿轮图标 → Add...
4. 选择 "Existing Environment"
5. 浏览选择: D:\Project\PycharmProjects\FastAPIProject\venv\Scripts\python.exe
6. 点击 OK
```

**5.2 重建缓存和索引**

```
1. File → Invalidate Caches...
2. 选择所有选项
3. 点击 "Invalidate and Restart"
```

### 步骤 6: 测试

在 IDE 中创建新文件 `test_pyspring.py`：

```python
from pyspring.log.loguru.logger import logger
from pyspring.ioc import ApplicationContext

# 应该有代码提示和自动补全
logger.info("Hello PySpring!")

# 初始化应用上下文
app_context = ApplicationContext.initialize(base_packages=[])
ioc = app_context.container
```

现在输入 `from pyspring.` 时应该能看到自动补全提示！

## 🔍 验证清单

- [ ] 虚拟环境已创建: `venv/` 目录存在
- [ ] 虚拟环境已激活: 命令提示符显示 `(venv)`
- [ ] PySpring 已安装在虚拟环境: `pip show pyspring` 有输出
- [ ] 诊断通过: `pyspring diagnose` 显示 "是否在虚拟环境: ✅ 是"
- [ ] IDE 解释器已设置: 指向 `venv\Scripts\python.exe`
- [ ] IDE 已重启: 重启语言服务器或完全重启
- [ ] 代码提示工作: 输入 `from pyspring.` 有自动补全

## 📊 对比：全局 vs 虚拟环境

| 特性     | 全局安装   | 虚拟环境（推荐） |
|--------|--------|----------|
| 命令行导入  | ✅ 可以   | ✅ 可以     |
| IDE 识别 | ❌ 不稳定  | ✅ 稳定     |
| 项目隔离   | ❌ 无    | ✅ 有      |
| 依赖管理   | ❌ 冲突风险 | ✅ 独立管理   |
| 团队协作   | ❌ 难以复现 | ✅ 易于复现   |
| 推荐度    | ❌ 不推荐  | ✅ 强烈推荐   |

## 🚫 常见错误

### 错误 1: 忘记激活虚拟环境

```powershell
# ❌ 错误
pip install pyspring  # 安装到全局

# ✅ 正确
venv\Scripts\Activate.ps1  # 先激活
pip install pyspring       # 再安装
```

### 错误 2: IDE 使用了错误的解释器

```
症状: pyspring diagnose 成功，但 IDE 报错
原因: IDE 使用了不同的 Python 解释器
解决: 在 IDE 中明确选择 venv\Scripts\python.exe
```

### 错误 3: 没有重启 IDE

```
症状: 配置了解释器但仍然报错
原因: IDE 缓存没有更新
解决: 
  VS Code: Ctrl+Shift+P → "Developer: Reload Window"
  PyCharm: File → Invalidate Caches / Restart
```

## 🎯 快速命令总结

```powershell
# 1. 创建并激活虚拟环境
cd D:\Project\PycharmProjects\FastAPIProject
python -m venv venv
venv\Scripts\Activate.ps1

# 2. 安装 PySpring
pip install pyspring

# 3. 验证
pyspring diagnose
python -c "from pyspring.log.loguru.logger import logger; print('✅')"

# 4. 在 IDE 中
# - 选择解释器: venv\Scripts\python.exe
# - 重启 IDE
```

## 📚 相关文档

- [诊断指南](DIAGNOSE_GUIDE.md) - 完整的诊断工具使用指南
- [在其他项目中使用](INSTALLATION_OTHER_PROJECT.md) - 详细安装配置
- [快速参考](QUICK_REFERENCE.md) - 常用命令速查

## 💡 提示

如果按照上述步骤仍然有问题，运行：

```powershell
# 在虚拟环境中
pyspring diagnose
```

新版的诊断工具会检测虚拟环境并给出针对性建议！
