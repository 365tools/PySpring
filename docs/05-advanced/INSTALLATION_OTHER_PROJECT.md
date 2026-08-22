# PySpring 在其他项目中使用指南

## 🚀 快速诊断

如果遇到导入问题，首先运行诊断命令：

```bash
pyspring check
```

这会自动检查：

- Python 环境信息
- PySpring 是否正确安装
- 导入是否正常
- Python 搜索路径
- 并提供具体的解决方案

## 问题诊断：为什么找不到包？

### 常见原因

1. **虚拟环境问题** - 最常见的原因！
    - 你在全局 Python 安装了 PySpring
    - 但在另一个项目中使用了虚拟环境
    - 虚拟环境中没有安装 PySpring

2. **IDE 解释器设置错误**
    - VS Code 或 PyCharm 使用了错误的 Python 解释器
    - IDE 没有自动识别虚拟环境

3. **多个 Python 版本**
    - 系统中安装了多个 Python
    - pip 安装到了不同的 Python 版本

## 解决方案

### 方案 1：在目标项目的虚拟环境中安装（推荐）

```bash
# 1. 进入你的目标项目目录
cd D:\YourProject

# 2. 创建虚拟环境（如果还没有）
python -m venv venv

# 3. 激活虚拟环境
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# 4. 在虚拟环境中安装 PySpring
pip install -e D:\Project\PycharmProjects\PySpring

# 5. 验证安装
python -c "from pyspring.log.loguru.logger import logger; print('✅ 成功!')"
```

### 方案 2：VS Code 配置

1. **选择正确的 Python 解释器**
   ```
   Ctrl+Shift+P → "Python: Select Interpreter"
   选择: .\venv\Scripts\python.exe
   ```

2. **检查 .vscode/settings.json**
   ```json
   {
       "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe"
   }
   ```

3. **重启 VS Code**
    - 有时需要完全重启 VS Code 才能识别新安装的包

### 方案 3：PyCharm 配置

1. **设置 Python 解释器**
   ```
   File → Settings → Project → Python Interpreter
   → Add Interpreter → Existing Environment
   → 选择: YourProject\venv\Scripts\python.exe
   ```

2. **标记源代码根目录**
   ```
   右键点击 PySpring/src → Mark Directory as → Sources Root
   ```

3. **重建索引**
   ```
   File → Invalidate Caches / Restart
   ```

## 验证安装的完整脚本

### 方法 1：命令行快速验证

```bash
# 检查 PySpring 是否安装
pip show pyspring

# 检查 Python 路径
python -c "import sys; print('\n'.join(sys.path))"

# 尝试导入
python -c "from pyspring.log.loguru.logger import logger; from pyspring.core.ioc import ApplicationContext; print('✅ 导入成功!')"
```

### 方法 2：使用测试脚本

```bash
# 方法 1: 使用 pyspring 命令（推荐）
pyspring check

# 方法 2: 从 PySpring 项目目录运行
python test_import_anywhere.py

# 方法 3: 从其他目录运行（测试真实场景）
cd D:\YourProject
python D:\Project\PycharmProjects\PySpring\test_import_anywhere.py
```

## 常见错误和解决方法

### 错误 1: ModuleNotFoundError: No module named 'pyspring'

**原因**: PySpring 没有安装在当前 Python 环境中

**解决**:

```bash
# 确认当前 Python
python -c "import sys; print(sys.executable)"

# 在当前环境安装
pip install -e D:\Project\PycharmProjects\PySpring
```

### 错误 2: 导入时没有代码提示/补全

**原因**: IDE 没有索引到包

**VS Code 解决**:

```bash
# 1. 确保选择了正确的解释器
Ctrl+Shift+P → Python: Select Interpreter

# 2. 重启 Pylance 语言服务器
Ctrl+Shift+P → Python: Restart Language Server

# 3. 重新加载窗口
Ctrl+Shift+P → Developer: Reload Window
```

**PyCharm 解决**:

```bash
File → Invalidate Caches / Restart → Invalidate and Restart
```

### 错误 3: 能导入但没有类型提示

**原因**: 类型存根 (stubs) 没有生成

**解决**:

```bash
# 重新安装
pip uninstall pyspring -y
pip install -e D:\Project\PycharmProjects\PySpring

# 重启 IDE
```

## 最佳实践

### 1. 项目结构

```
YourProject/
├── venv/                    # 虚拟环境
├── src/
│   └── your_code.py
├── requirements.txt         # 依赖列表
└── .vscode/
    └── settings.json        # VS Code 配置
```

### 2. requirements.txt

```txt
# 开发环境：使用本地可编辑安装
-e D:\Project\PycharmProjects\PySpring

# 生产环境：使用 Git 安装
# git+https://github.com/eavelabs-community/py-spring.git
```

### 3. 使用示例

```python
# your_code.py
from pyspring.log.loguru.logger import logger
from pyspring.core.ioc import ApplicationContext

# 初始化 IoC 容器
app_context = ApplicationContext.initialize(base_packages=["your_app.services"])

# 使用日志
logger.info("✅ PySpring 初始化成功")

# 获取服务
cache_service = ioc_manager.get_service("cache_manager_service")
logger.info(f"缓存服务: {cache_service}")
```

## 调试技巧

### 1. 打印调试信息

```python
import sys
import pyspring

print(f"Python 可执行文件: {sys.executable}")
print(f"PySpring 位置: {pyspring.__file__}")
print(f"PySpring 路径: {pyspring.__path__}")
```

### 2. 检查虚拟环境

```bash
# Windows
where python
where pip

# Linux/Mac
which python
which pip
```

### 3. 检查安装的包

```bash
pip list | grep pyspring
pip show pyspring
```

## 完整的新项目设置流程

```bash
# 1. 创建项目
mkdir MyNewProject
cd MyNewProject

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
venv\Scripts\Activate.ps1  # Windows PowerShell

# 4. 安装 PySpring
pip install -e D:\Project\PycharmProjects\PySpring

# 5. 创建测试文件
echo 'from pyspring.log.loguru.logger import logger; logger.info("Hello PySpring!")' > test.py

# 6. 运行测试
python test.py

# 7. 在 VS Code 中打开
code .

# 8. 选择 Python 解释器
# Ctrl+Shift+P → Python: Select Interpreter → .\venv\Scripts\python.exe
```

## 还是不行？

如果按照上述步骤还是不行，请提供以下信息：

```bash
# 运行以下命令并提供输出
python --version
python -c "import sys; print(sys.executable)"
pip show pyspring
python -c "import sys; print('\n'.join(sys.path[:5]))"
```

然后检查：

1. 你在哪个目录运行的命令？
2. 是否在虚拟环境中？
3. IDE 使用的是哪个 Python 解释器？

---

**提示**: 最常见的问题就是虚拟环境！确保在正确的虚拟环境中安装和运行。
