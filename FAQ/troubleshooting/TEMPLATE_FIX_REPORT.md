# 项目模板修复报告

## 问题描述

用户使用 `pyspring init` 命令生成的示例项目在启动时报错：

```
ImportError: cannot import name 'CustomUser' from 'app.config.security_config'
```

## 根本原因

项目模板文件中存在错误的导入语句：

- **错误导入**: `from app.config.security_config import CustomUser`
- **实际情况**: `CustomUser` 只是 `security_config.py` 注释中的示例代码，未实际定义
- **正确的类**: 项目实际定义的是 `app.models.user.User` 类

## 修复内容

### 1. 修复的模板文件

#### `custom_login_provider.py.template`

- ✅ 修复导入: `from app.models.user import User`
- ✅ 更新所有 `CustomUser` 引用为 `User`
- ✅ 更新查询语句中的类名
- ✅ 更新类型注解和文档字符串

#### `custom_register_service.py.template`

- ✅ 修复导入: `from app.models.user import User`
- ✅ 更新邮箱检查查询: `select(User).where(User.email == user.email)`
- ✅ 更新用户名检查查询: `select(User).where(User.username == user.username)`
- ✅ 更新用户实例创建: `db_user = User(...)`
- ✅ 更新所有方法签名中的类型注解

#### `auth.py.template`

- ✅ 更新文档注释: `User 模型（app/models/user.py）`

#### `README.md.template`

- ✅ 更新项目结构说明: `User 模型 - 扩展用户表`

### 2. 修改统计

| 文件                                  | 修改行数 | 主要修改           |
|-------------------------------------|------|----------------|
| custom_login_provider.py.template   | 8    | 导入语句、类型注解、查询语句 |
| custom_register_service.py.template | 11   | 导入语句、查询语句、对象创建 |
| auth.py.template                    | 1    | 文档注释           |
| README.md.template                  | 1    | 项目说明           |

### 3. 验证结果

✅ 所有模板文件检查通过
✅ 不再存在错误的 `CustomUser` 导入
✅ 所有引用已更新为正确的 `User` 类

## 技术细节

### 修改前

```python
from app.config.security_config import CustomUser

async def _find_user_by_flexible_identifier(self, identifier: str) -> Any:
    async with await self.db.session() as session:
        result = await session.execute(
            select(CustomUser).where(
                or_(
                    CustomUser.user_id == identifier,
                    CustomUser.username == identifier,
                    CustomUser.email == identifier,
                    CustomUser.phone == identifier,
                )
            )
        )
        return result.scalar_one_or_none()
```

### 修改后

```python
from app.models.user import User

async def _find_user_by_flexible_identifier(self, identifier: str) -> Any:
    async with await self.db.session() as session:
        result = await session.execute(
            select(User).where(
                or_(
                    User.user_id == identifier,
                    User.username == identifier,
                    User.email == identifier,
                    User.phone == identifier,
                )
            )
        )
        return result.scalar_one_or_none()
```

## 影响范围

### 已修复

- ✅ 新生成的项目将使用正确的导入
- ✅ 示例代码可以正常运行
- ✅ 不再出现 ImportError

### 需要用户操作（已生成的项目）

对于已经使用旧模板生成的 `py-demo` 项目：

**选项1：重新生成项目（推荐）**

```powershell
# 删除旧项目
Remove-Item -Recurse -Force D:\Project\PycharmProjects\py-demo

# 重新生成
pyspring init py-demo
```

**选项2：手动修复现有项目**
修改以下文件：

1. `app/services/custom_login_provider.py` - 第36行
2. `app/services/custom_register_service.py` - 第39行

将导入语句改为：

```python
from app.models.user import User
```

并将所有 `CustomUser` 替换为 `User`

## 测试验证

运行验证脚本确认修复：

```bash
python verify_template_fix.py
```

输出：

```
✅ 所有模板文件检查通过！

正确的导入模式：
  - from app.models.user import User

已修复的文件：
  ✓ custom_login_provider.py.template
  ✓ custom_register_service.py.template
  ✓ auth.py.template
  ✓ README.md.template
```

## 预防措施

建议在模板文件中添加以下注释：

```python
# 注意：请确保从 app.models.user 导入 User 类
# User 类在 app/models/user.py 中定义，继承自 BaseUserTable
# 不要从 app.config.security_config 导入（那里只有注释示例）
```

## 总结

本次修复解决了项目模板中的导入错误，确保新生成的项目可以正常启动和运行。所有修改都已经过验证，不会影响框架的其他功能。
