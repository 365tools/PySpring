# Services 说明

本目录包含示例服务，展示 PySpring 框架的各种功能。

## 📁 文件说明

### 核心业务服务

- **`user_service.py`** - 用户业务服务
    - 展示：@Component 装饰器、依赖注入、缓存集成
    - 状态：**✅ 正常使用**

- **`cache_service.py`** - 缓存服务封装
    - 展示：CacheManagerService 使用、多级缓存
    - 状态：**✅ 正常使用**

- **`health_check_service.py`** - 健康检查服务
    - 展示：健康检查实现
    - 状态：**✅ 正常使用**

- **`auth_service.py`** - 认证服务
    - 展示：JWT Token 生成、密码验证、用户认证
    - 状态：**✅ 正常使用**

### 框架扩展示例

- **`custom_register_service.py`** - 自定义注册服务
    - 展示：继承 DefaultRegisterService、自定义字段处理
    - 状态：**✅ 正常使用**（示范如何扩展框架）

- **`custom_login_provider.py`** - 自定义登录提供者
    - 展示：继承 DefaultPasswordLoginProvider、添加自定义逻辑
    - 状态：**⚠️ 可选示例（默认禁用）**

## ⚠️ custom_login_provider.py 使用说明

**这是一个可选的高级自定义示例，默认情况下不启用。**

### 何时需要自定义？

大多数情况下**不需要**自定义！框架从 v1.1.0 开始已支持配置化登录字段：

```yaml
# config/security.yaml
authentication:
  identifier_fields:
    - "username"
    - "email"
    - "phone"
```

仅在以下情况需要自定义：

- ✅ 添加登录前后的业务逻辑（如记录登录日志、发送通知）
- ✅ 集成第三方认证服务（如 OAuth2、LDAP）
- ✅ 自定义密码验证规则（如多因素认证）

### 如何启用？

1. **打开文件** `app/services/custom_login_provider.py`
2. **取消注释** `@Component` 装饰器（第 45 行左右）
3. **根据需要修改** `authenticate()` 方法中的自定义逻辑
4. **重启应用**

### ⚠️ 常见问题

**Q: 为什么会提示 "服务已注册" 错误？**

A: 如果你的项目中同时存在以下文件：

- `custom_login_provider.py`
- `custom_login_provider_example.py`

并且两个文件都定义了 `CustomPasswordLoginProvider` 类且都启用了 `@Component`，会导致重复注册。

**解决方案：**

- 删除其中一个文件（推荐保留 `custom_login_provider.py`）
- 或者确保只有一个文件启用了 `@Component` 装饰器

---

## 📝 添加新服务

创建新服务的步骤：

1. 在 `app/services/` 目录下创建新文件，如 `my_service.py`
2. 定义服务类并使用 `@Component` 装饰器：

```python
from pyspring.ioc import Component

@Component
class MyService:
    def __init__(self, dependency: SomeDependency):
        self.dependency = dependency
    
    async def do_something(self):
        # 业务逻辑
        pass
```

3. 框架会自动扫描并注册该服务
4. 在其他地方通过依赖注入使用：

```python
@Component
class OtherService:
    def __init__(self, my_service: MyService):
        self.my_service = my_service
```

---

## 🔗 相关文档

- [PySpring IoC 容器文档](../../docs/02-core-concepts/dependency-injection.md)
- [认证扩展指南](../../docs/SECURITY_EXTENSION_GUIDE.md)
- [最佳实践](../../docs/README.md)
