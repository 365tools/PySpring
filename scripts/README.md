# PySpring Scripts

本目录包含PySpring框架开发和维护所需的各种工具脚本。

## 📁 目录结构

### 🛠️ [utilities](./utilities/) - 实用工具

开发和维护过程中常用的工具脚本。

#### 数据库工具

- **check_orm_models.py** - 检查ORM模型是否正确注册到SQLAlchemy的Base.metadata
- **init_database.py** - 通过IoC容器初始化数据库（推荐方式）
- **create_tables.py** - 强制创建所有数据库表（直接使用SQLAlchemy）

#### 代码清理工具

- **clean_emojis.py** - 批量清理代码中的emoji，替换为文本标记
- **fix_garbled_text.py** - 修复文件中的乱码文本

#### 项目修复工具

- **fix_existing_project.py** - 修复使用旧模板生成的项目（例如CustomUser导入问题）

#### 测试工具

- **run_quick_test.py** - 快速运行特定的测试用例

### � [development](./development/) - 开发脚本

开发过程中使用的自动化脚本。

- **fix_example_project.ps1** - 修复示例项目的缓存和依赖问题

### �🔍 [diagnostics](./diagnostics/) - 诊断工具

用于诊断框架和示例项目问题的脚本。

#### 项目诊断

- **diagnose_demo.py** - 诊断py-demo示例项目中的问题
- **diagnose_example_config.py** - 诊断示例配置文件的问题

#### 验证工具

- **verify_framework.py** - 验证框架核心文件的语法和导入完整性
- **verify_complete_fix.py** - 验证项目模板修复是否完整
- **verify_db_schema.py** - 验证数据库表结构是否正确
- **verify_authorization_refactor.py** - 验证授权模块重构
- **verify_template_fix.py** - 验证项目模板修复

## 🚀 使用方法

### 数据库初始化

推荐使用IoC容器方式：

```bash
python scripts/utilities/init_database.py
```

或者直接创建表：

```bash
python scripts/utilities/create_tables.py
```

### 检查ORM模型

```bash
python scripts/utilities/check_orm_models.py
```

### 诊断项目问题

诊断示例项目配置：

```bash
python scripts/diagnostics/diagnose_example_config.py
```

验证框架完整性：

```bash
python scripts/diagnostics/verify_framework.py
```

### 修复旧项目

修复使用旧模板生成的项目：

```bash
python scripts/utilities/fix_existing_project.py <项目路径>
```

### 代码清理

批量清理emoji：

```bash
python scripts/utilities/clean_emojis.py
```

## 📝 脚本开发规范

开发新的工具脚本时，请遵循以下规范：

1. **文件命名**：使用小写字母和下划线，清晰描述功能
2. **文档字符串**：每个脚本顶部包含清晰的用途说明
3. **错误处理**：妥善处理异常情况，提供友好的错误信息
4. **日志输出**：使用统一的格式输出执行进度和结果
5. **参数验证**：对输入参数进行验证

### 脚本模板

```python
"""
脚本用途简短描述

详细说明脚本的功能、使用场景等
"""
import os
import sys


def main():
    """主函数"""
    print("=" * 80)
    print("脚本名称")
    print("=" * 80)
    
    # 具体实现
    pass


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)
```

## 🔧 维护说明

- 定期清理过时的脚本
- 更新脚本以适配框架的变化
- 在修改重要脚本前做好备份
- 及时更新本README文档

## 🤝 贡献

如果您开发了有用的工具脚本，欢迎贡献到本目录：

1. 确保脚本符合开发规范
2. 添加完整的文档说明
3. 在本README中添加相应的说明
4. 提交Pull Request
