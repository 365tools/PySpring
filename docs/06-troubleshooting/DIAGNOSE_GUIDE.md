# PySpring 诊断命令使用指南

## 问题场景

当你在其他项目中使用 PySpring 时遇到导入错误：

```python
from pyspring.log.loguru.logger import logger
# ModuleNotFoundError: No module named 'pyspring'
```

## 快速诊断

只需运行一个命令：

```bash
pyspring check
```

## 诊断输出示例

### ✅ 正常情况

```
======================================================================
PySpring 导入问题诊断
======================================================================

======================================================================
1. Python 环境信息
======================================================================
Python 可执行文件: /path/to/venv/bin/python
Python 版本: 3.12.10
当前工作目录: /path/to/your/project
是否在虚拟环境: ✅ 是
虚拟环境路径: /path/to/venv

======================================================================
2. PySpring 安装检查
======================================================================
✅ PySpring 已安装
   Version: 1.0.0
   Location: /path/to/venv/lib/python3.12/site-packages

======================================================================
3. 导入测试
======================================================================
测试: import pyspring
✅ 成功
   位置: /path/to/venv/lib/python3.12/site-packages/pyspring/__init__.py

测试具体模块:
✅ pyspring.log.loguru.logger.logger
✅ pyspring.core.ioc.ApplicationContext

======================================================================
4. Python 搜索路径
======================================================================
前 10 个路径:
   1. /path/to/venv/bin
   2. /usr/lib/python3.12
   3. /path/to/venv/lib/python3.12/site-packages
   ...

======================================================================
诊断结果
======================================================================
🎉 PySpring 工作正常！可以开始使用了。

示例代码:
```python
from pyspring.log.loguru.logger import logger
from pyspring.core.ioc import ApplicationContext

logger.info('Hello PySpring!')
# 注意：需要先初始化应用上下文
app_context = ApplicationContext.initialize(base_packages=[])
```

```

### ❌ 问题情况

```

======================================================================
PySpring 导入问题诊断
======================================================================

======================================================================

1. Python 环境信息
   ======================================================================
   Python 可执行文件: C:\Python312\python.exe
   Python 版本: 3.12.10
   当前工作目录: D:\YourProject
   是否在虚拟环境: ❌ 否

======================================================================

2. PySpring 安装检查
   ======================================================================
   ❌ PySpring 未安装

💡 请运行: pip install pyspring
或开发模式: pip install -e /path/to/PySpring

======================================================================

3. 导入测试
   ======================================================================
   测试: import pyspring
   ❌ 失败: No module named 'pyspring'

======================================================================

5. 解决方案
   ======================================================================
   ⚠️ 你不在虚拟环境中！

推荐步骤:

1. 创建虚拟环境:
   python -m venv venv

2. 激活虚拟环境:
   Windows PowerShell: venv\Scripts\Activate.ps1
   Windows CMD: venv\Scripts\activate.bat
   Linux/Mac: source venv/bin/activate

3. 安装 PySpring:
   pip install pyspring
   # 或开发模式: pip install -e /path/to/PySpring

4. 在 VS Code 中:
    - Ctrl+Shift+P → 'Python: Select Interpreter'
    - 选择虚拟环境的 Python
    - 重启 VS Code

5. 验证:
   python -c "from pyspring.log.loguru.logger import logger; print('✅ 成功!')"
   或运行: pyspring check

```

## 常见问题和解决方案

### 1. 不在虚拟环境中

**问题**: `是否在虚拟环境: ❌ 否`

**解决**:
```bash
# 创建虚拟环境
cd YourProject
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\Activate.ps1

# 安装 PySpring
pip install pyspring

# 验证
pyspring check
```

### 2. PySpring 未安装

**问题**: `❌ PySpring 未安装`

**解决**:

```bash
# 确保在正确的虚拟环境中
which python  # Linux/Mac
where python  # Windows

# 安装 PySpring
pip install pyspring

# 或从源码安装（开发模式）
pip install -e /path/to/PySpring

# 验证
pyspring check
```

### 3. 导入失败但已安装

**问题**: PySpring 已安装但导入失败

**可能原因**:

- IDE 使用了不同的 Python 解释器
- 缓存问题

**解决**:

```bash
# 1. 重新安装
pip uninstall pyspring -y
pip install pyspring

# 2. VS Code 重新选择解释器
Ctrl+Shift+P → "Python: Select Interpreter"

# 3. 重启 VS Code
Ctrl+Shift+P → "Developer: Reload Window"

# 4. PyCharm 重建索引
File → Invalidate Caches / Restart

# 5. 再次诊断
pyspring check
```

### 4. 多个 Python 版本

**问题**: 系统中有多个 Python 版本

**解决**:

```bash
# 查看当前 Python
python --version
python -c "import sys; print(sys.executable)"

# 明确指定 Python 版本
python3.12 -m venv venv
venv\Scripts\python.exe -m pip install pyspring

# 在项目中使用该 Python
venv\Scripts\python.exe your_script.py
```

## 在 VS Code 中配置

### 1. 选择正确的解释器

```
Ctrl+Shift+P → "Python: Select Interpreter"
选择: .\venv\Scripts\python.exe
```

### 2. 配置 settings.json

在项目的 `.vscode/settings.json` 中：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
    "python.terminal.activateEnvironment": true
}
```

### 3. 重启 Python 语言服务器

```
Ctrl+Shift+P → "Python: Restart Language Server"
```

### 4. 完全重新加载

```
Ctrl+Shift+P → "Developer: Reload Window"
```

## 在 PyCharm 中配置

### 1. 设置项目解释器

```
File → Settings → Project → Python Interpreter
→ Add Interpreter → Existing Environment
→ 选择: YourProject\venv\Scripts\python.exe
```

### 2. 重建缓存

```
File → Invalidate Caches / Restart → Invalidate and Restart
```

## 完整的项目设置流程

### 新项目从零开始

```bash
# 1. 创建项目目录
mkdir MyProject
cd MyProject

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
venv\Scripts\Activate.ps1  # Windows PowerShell
# 或
source venv/bin/activate    # Linux/Mac

# 4. 安装 PySpring
pip install pyspring

# 5. 初始化项目
pyspring init

# 6. 诊断确认
pyspring check

# 7. 在 VS Code 中打开
code .

# 8. 选择解释器
# Ctrl+Shift+P → Python: Select Interpreter → .\venv\Scripts\python.exe

# 9. 运行项目
python main.py
```

## 高级用法

### 开发模式安装

如果你需要修改 PySpring 源码：

```bash
# 克隆仓库
git clone https://github.com/eavelabs-community/py-spring.git

# 安装为可编辑模式
cd YourProject
source venv/bin/activate  # 激活项目的虚拟环境
pip install -e /path/to/PySpring

# 修改 PySpring 代码后无需重新安装，直接生效
pyspring check
```

### 持续集成 (CI)

在 CI 环境中使用诊断：

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install pyspring
      
      - name: Diagnose
        run: |
          source venv/bin/activate
          pyspring check
      
      - name: Run tests
        run: |
          source venv/bin/activate
          python -m pytest
```

## 相关文档

- [在其他项目中使用 PySpring](INSTALLATION_OTHER_PROJECT.md) - 完整的安装和配置指南
- [安装指南](INSTALLATION_GUIDE.md) - PySpring 基础安装
- [快速参考](QUICK_REFERENCE.md) - 常用命令速查

## 需要帮助？

如果诊断后仍然有问题，请提供以下信息：

```bash
# 运行这些命令并提供输出
pyspring check
python --version
pip show pyspring
pip list | grep pyspring
```

然后在 GitHub 上创建 Issue：https://github.com/eavelabs-community/py-spring/issues

---

**提示**: `pyspring check` 是排查问题的第一步，它会自动检查并给出具体的解决方案！
