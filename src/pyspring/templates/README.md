# PySpring 模板目录结构

此目录包含 PySpring 项目初始化所需的所有模板文件。

## 📁 目录结构

```
templates/
├── config/              # 配置文件模板
│   ├── container.yaml
│   ├── logging.yaml
│   ├── repositories.yaml
│   └── security.yaml
├── app/                 # 应用程序模板
│   └── main.py.template
├── project/             # 项目配置模板
│   ├── pyproject.toml.template
│   └── .gitignore.template
└── README.md           # 本文件
```

## 🎯 设计目的

### 自动化扫描

- `config/` 目录中的所有 `.yaml` 文件会被自动扫描
- 添加新的配置文件模板时，**无需修改代码**
- `init.py` 会自动发现并包含新的配置文件

### 分类管理

- **config/**: 应用配置文件（YAML 格式）
- **app/**: 应用程序代码模板
- **project/**: 项目级别的配置文件

## ➕ 如何添加新的配置模板

### 1. 添加配置文件

直接在 `config/` 目录中创建新的 `.yaml` 文件：

```bash
# 例如添加 cache.yaml
echo "# Cache configuration" > config/cache.yaml
```

### 2. 更新描述（可选）

如果需要自定义描述，编辑 `init.py` 中的 `get_config_files_from_templates()` 函数：

```python
config_descriptions = {
    "container.yaml": "IoC 容器配置",
    "logging.yaml": "日志配置",
    "repositories.yaml": "数据库与缓存配置",
    "security.yaml": "认证与授权配置",
    "cache.yaml": "缓存配置",  # 添加新的描述
}
```

### 3. 自动生效

运行 `pyspring init` 时，新的配置文件会自动被包含：

```bash
pyspring init
```

## 🔧 模板文件命名规范

### Config 模板

- **格式**: `*.yaml`
- **位置**: `templates/config/`
- **示例**: `container.yaml`, `logging.yaml`

### App 模板

- **格式**: `*.template`
- **位置**: `templates/app/`
- **示例**: `main.py.template`

### Project 模板

- **格式**: `*.template`
- **位置**: `templates/project/`
- **示例**: `pyproject.toml.template`, `.gitignore.template`

## 📝 模板文件内容指南

### Config 模板（YAML）

```yaml
# 文件头部应包含清晰的注释
# 说明配置的用途和使用方法

key:
  # 每个配置项都应有注释
  sub_key: "value"
  
  # 提供使用示例
  # 示例: 
  #   option: "example"
```

### App 模板

```python
"""
模块说明文档
"""

# 标准的 Python 代码模板
# 包含最佳实践和推荐用法
```

## 🎨 模板变量替换

某些模板文件支持变量替换：

- `pyproject.toml.template`:
    - `name = "pyspring"` → `name = "my-pyspring-app"`
    - 作者信息替换为占位符
    - URL 替换为用户项目

## 🚀 使用示例

### 完整初始化

```bash
pyspring init /path/to/project
```

### 最小化初始化（仅 security.yaml）

```bash
pyspring init --minimal
```

### 强制覆盖现有文件

```bash
pyspring init --force
```

## 📦 模板更新流程

1. **更新模板文件**: 直接修改 `templates/` 下的文件
2. **测试验证**: 运行 `pyspring init` 测试
3. **版本控制**: 提交更改到 Git
4. **发布**: 新版本的 PySpring 会包含更新的模板

## 🔍 调试技巧

### 查看扫描到的配置文件

```python
from pyspring.init import get_config_files_from_templates

config_files = get_config_files_from_templates()
print(config_files)
# 输出: [('container.yaml', 'IoC 容器配置'), ...]
```

### 检查模板路径

```python
from pyspring.init import get_template_dir

template_dir = get_template_dir()
print(template_dir / "config")
# 输出: /path/to/pyspring/templates/config
```

## 📋 配置文件说明

| 文件                  | 说明       | 必需 |
|---------------------|----------|----|
| `container.yaml`    | IoC 容器配置 | 否  |
| `logging.yaml`      | 日志系统配置   | 是  |
| `repositories.yaml` | 数据库与缓存配置 | 是  |
| `security.yaml`     | 认证与授权配置  | 是  |

## 🎯 最佳实践

1. **保持简洁**: 模板应该包含合理的默认值
2. **详细注释**: 每个配置项都应有清晰的说明
3. **环境感知**: 提供开发/测试/生产环境的配置示例
4. **安全优先**: 敏感信息使用环境变量
5. **向后兼容**: 更新模板时考虑已有项目

## 🔗 相关文档

- [PySpring 初始化工具](../init.py)
- [配置指南](../../../docs/README.md)
- [快速开始](../../../README.md)
