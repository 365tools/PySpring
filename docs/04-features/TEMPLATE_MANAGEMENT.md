# PySpring 模板文件管理

## 模板文件位置

所有模板文件位于 `src/pyspring/templates/` 目录：

```
src/pyspring/templates/
├── .gitignore.template          # Git 忽略规则模板
├── pyproject.toml.template      # Python 项目配置模板
├── container.yaml               # IoC 容器配置模板
├── logging.yaml                 # 日志配置模板
├── repositories.yaml            # 数据库与缓存配置模板
└── security.yaml                # 认证与授权配置模板
```

## 模板文件来源

### 1. .gitignore.template

- **来源**: 复制自 PySpring 根目录的 `.gitignore`
- **更新方式**:
  ```bash
  Copy-Item ".gitignore" "src\pyspring\templates\.gitignore.template"
  ```
- **用途**: 为新项目提供完整的 Python 生态工具支持

### 2. pyproject.toml.template

- **来源**: 复制自 PySpring 根目录的 `pyproject.toml`
- **更新方式**:
  ```bash
  Copy-Item "pyproject.toml" "src\pyspring\templates\pyproject.toml.template"
  ```
- **用途**: 为新项目提供标准的依赖配置
- **自动替换**:
    - `name = "pyspring"` → `name = "my-pyspring-app"`
    - 作者信息 → 占位符
    - 项目 URL → 占位符
    - 移除 pyspring CLI 入口

### 3. YAML 配置模板

- **来源**: 手动维护的标准配置
- **用途**: 为新项目提供框架功能配置

## 打包配置

在 `pyproject.toml` 中配置模板文件打包：

```toml
[tool.setuptools.package-data]
pyspring = [
    "templates/*.yaml",
    "templates/pyproject.toml.template",
    "templates/.gitignore.template"
]
```

## init.py 实现

### create_gitignore()

```python
def create_gitignore(target_dir: Path):
    """从模板读取"""
    template_path = get_template_dir() / ".gitignore.template"
    content = template_path.read_text(encoding="utf-8")
    gitignore_path.write_text(content, encoding="utf-8")
```

### create_pyproject_toml()

```python
def create_pyproject_toml(target_dir: Path):
    """从模板读取并替换项目信息"""
    template_path = get_template_dir() / "pyproject.toml.template"
    content = template_path.read_text(encoding="utf-8")

    # 替换项目名称
    content = content.replace('name = "pyspring"', 'name = "my-pyspring-app"')
    # 替换作者信息
    content = content.replace(
        '{ name="eavelabs", email="365tools.t1@gmail.com" }', '{ name="Your Name", email="your.email@example.com" }'
    )
    # 替换项目 URL
    content = content.replace(
        '"Homepage" = "https://github.com/eavelabs-community/py-spring"',
        '"Homepage" = "https://github.com/yourusername/my-pyspring-app"',
    )

    pyproject_path.write_text(content, encoding="utf-8")
```

## 模板更新流程

### 开发阶段

1. 直接修改 `pyproject.toml` 和 `.gitignore`
2. 执行更新命令将变更同步到模板：
   ```bash
   # 更新 .gitignore 模板
   Copy-Item ".gitignore" "src\pyspring\templates\.gitignore.template"
   
   # 更新 pyproject.toml 模板
   Copy-Item "pyproject.toml" "src\pyspring\templates\pyproject.toml.template"
   ```

### 打包发布

1. 确保模板文件已更新
2. 执行打包命令：
   ```bash
   python -m build
   ```
3. 模板文件会被自动包含到发行包中

### 安装后使用

1. 用户安装 pyspring 包
2. 执行 `pyspring init`
3. 自动从 site-packages 中读取模板文件
4. 生成新项目结构

## 优势

✅ **单一数据源**: 模板文件在 PySpring 项目中维护  
✅ **自动同步**: 更新项目配置后手动同步到模板  
✅ **打包简单**: setuptools 自动处理模板文件  
✅ **无容错逻辑**: 简洁直接，模板必须存在

## 注意事项

1. **模板文件必须存在**: 如果缺失会导致 init 命令失败
2. **手动同步**: 修改根目录配置后需要手动同步到 templates
3. **版本控制**: 模板文件应该纳入 Git 版本控制
4. **测试验证**: 每次更新模板后应测试 init 命令

## 测试命令

```bash
# 测试模板文件是否存在
python -c "from pyspring.init import get_template_dir; print(get_template_dir())"

# 测试 init 命令
pyspring init test_project

# 验证生成的文件
cd test_project
cat .gitignore | head -20
cat pyproject.toml
```

## 未来改进

可以创建一个自动化脚本定期同步模板：

```python
# sync_templates.py
from pathlib import Path
import shutil

root = Path(__file__).parent
templates = root / "src/pyspring/templates"

# 同步文件
shutil.copy2(root / ".gitignore", templates / ".gitignore.template")
shutil.copy2(root / "pyproject.toml", templates / "pyproject.toml.template")

print("✅ 模板文件已同步")
```

使用：

```bash
python sync_templates.py
```
