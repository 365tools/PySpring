# PySpring Security: 默认实现与用户自定义扩展机制详解

## 核心机制：@ConditionalOnMissingBean

PySpring Security使用IOC容器的**条件注册**机制实现默认实现与用户自定义的无缝切换。

### 工作原理

```python
@Bean()
@ConditionalOnMissingBean(IUserProvider)  # ← 关键：只在用户没定义时才注册
def default_user_provider(...) -> IUserProvider:
    return DefaultUserProvider(...)
```

**执行逻辑：**
1. IOC容器启动时，扫描所有`@Bean`方法
2. 检查是否已存在`IUserProvider`类型的Bean
3. 如果**不存在** → 注册默认实现
4. 如果**已存在** → 跳过默认实现，使用用户自定义

---

## 一、认证（Authentication）的默认与自定义

### 1.1 默认认证流程

```
用户登录请求
    ↓
ILoginService (默认: DefaultLoginService)
    ↓
List<ILoginProvider> (默认: [DefaultPasswordLoginProvider])
    ↓ 遍历查找支持的Provider
DefaultPasswordLoginProvider
    ↓ 验证密码
IUserProvider (默认: DefaultUserProvider)
    ↓ 查询数据库
ITokenService (默认: TokenService)
    ↓ 生成Token
IResponseBuilder (默认: DefaultResponseBuilder)
    ↓
返回登录响应
```

### 1.2 默认认证组件配置

```python
# authentication/config/auto_config.py

@Configuration
class AuthenticationConfiguration:
    
    # 1️⃣ 用户提供者（查询用户）
    @Bean()
    @ConditionalOnMissingBean(IUserProvider)
    def default_user_provider(self, db, component) -> IUserProvider:
        return DefaultUserProvider(db, component)  # 数据库查询
    
    # 2️⃣ 登录提供者（密码验证）
    @Bean()
    @ConditionalOnMissingBean(ILoginProvider)
    def default_login_providers(self, password_provider) -> List[ILoginProvider]:
        return [password_provider]  # 支持密码登录
    
    # 3️⃣ Token服务（生成Token）
    @Bean()
    @ConditionalOnMissingBean(ITokenService)
    def default_token_service(self) -> ITokenService:
        return TokenService()  # JWT Token
    
    # 4️⃣ 登录服务（编排流程）
    @Bean()
    @ConditionalOnMissingBean(ILoginService)
    def default_login_service(self, user_provider, login_providers, ...) -> ILoginService:
        return DefaultLoginService(user_provider, login_providers, ...)
```

---

### 1.3 用户自定义认证（5种方式）

#### 方式1⃣️：自定义ILoginProvider（添加认证方式）

```python
# 场景：添加LDAP登录支持

from pyspring.ioc.annotations.component import Component
from pyspring.security.authentication.contracts.login import ILoginProvider

@Component()  # ← 自动注册为Bean
class LDAPLoginProvider(ILoginProvider):
    """LDAP登录提供者"""
    
    def __init__(self, ldap_client):
        self.ldap_client = ldap_client
    
    def supports(self, request) -> bool:
        """检查是否支持此请求"""
        return request.login_type == "ldap"
    
    async def authenticate(self, request):
        """LDAP认证逻辑"""
        # 1. 连接LDAP服务器验证
        ldap_user = await self.ldap_client.authenticate(
            request.username, 
            request.password
        )
        
        # 2. 映射到本地用户
        return await self.user_repo.find_by_email(ldap_user.email)

# ✅ 自动生效：DefaultLoginService会自动收集所有ILoginProvider
# 现在支持：[DefaultPasswordLoginProvider, LDAPLoginProvider]
```

#### 方式2⃣️：完全替换ILoginService（控制整个登录流程）

```python
# 场景：自定义登录逻辑（如添加验证码）

from pyspring.ioc.annotations.component import Bean
from pyspring.security.authentication.contracts.flow import ILoginService

@Bean()  # ← 注意：不需要@ConditionalOnMissingBean
def custom_login_service(...) -> ILoginService:
    """自定义登录服务"""
    
    class CustomLoginService(ILoginService):
        async def login(self, request):
            # 1. 验证验证码
            if not await self.verify_captcha(request.captcha):
                raise Exception("验证码错误")
            
            # 2. 调用原有逻辑
            return await self.default_login_service.login(request)
    
    return CustomLoginService(...)

# ✅ 效果：框架的 default_login_service 不会注册（因为已存在ILoginService Bean）
```

#### 方式3⃣️：自定义IUserProvider（更换用户来源）

```python
# 场景：从Redis读取用户而非MySQL

from pyspring.security.authentication.contracts.user import IUserProvider

@Component()
class RedisUserProvider(IUserProvider):
    """从Redis读取用户"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def find_user_by_username(self, username):
        user_data = await self.redis.hgetall(f"user:{username}")
        return User(**user_data) if user_data else None

# ✅ 效果：DefaultUserProvider 不会注册，使用RedisUserProvider
```

#### 方式4⃣️：自定义ITokenGenerator（更换Token类型）

```python
# 场景：使用Session Token替代JWT

from pyspring.security.authentication.contracts.token import ITokenGenerator

@Component()
class SessionTokenGenerator(ITokenGenerator):
    """Session Token生成器"""
    
    def encode(self, payload, expires_delta):
        session_id = str(uuid.uuid4())
        # 存储到Redis
        await self.redis.setex(
            f"session:{session_id}",
            expires_delta.total_seconds(),
            json.dumps(payload)
        )
        return session_id
    
    def decode(self, token):
        data = await self.redis.get(f"session:{token}")
        return json.loads(data) if data else None
    
    def get_token_type(self):
        return "Session"

# ✅ 效果：TokenService会使用SessionTokenGenerator而非JWTTokenGenerator
```

#### 方式5⃣️：自定义IPasswordEncoder（更换密码算法）

```python
# 场景：使用Argon2替代BCrypt

from pyspring.security.authentication.contracts.password import IPasswordEncoder
import argon2

@Component()
class Argon2PasswordEncoder(IPasswordEncoder):
    """Argon2密码编码器（更强的安全性）"""
    
    def __init__(self):
        self.hasher = argon2.PasswordHasher()
    
    def encode(self, raw_password: str) -> str:
        return self.hasher.hash(raw_password)
    
    def verify(self, raw_password: str, encoded_password: str) -> bool:
        try:
            self.hasher.verify(encoded_password, raw_password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False

# ✅ 效果：所有密码验证使用Argon2
```

---

## 二、授权（Authorization）的默认与自定义

### 2.1 默认授权流程

```
权限检查请求
    ↓
IPermissionService (默认: DefaultPermissionService)
    ↓ has_permission(user_id, "user:read")
IRoleProvider (默认: DefaultRoleProvider)
    ↓ 查询用户角色
get_effective_roles(user_id)  # 包含继承
    ↓ 返回 ['admin', 'manager', 'user']
get_role_permissions('admin')  # 查询角色权限
    ↓ 返回 ['admin:*', 'user:*']
权限匹配（支持通配符）
    ↓
返回 True/False
```

### 2.2 默认授权组件配置

```python
# authorization/config/auto_config.py

@Configuration
class AuthorizationConfiguration:
    
    # 1️⃣ 角色提供者（查询角色和权限）
    @Bean
    @ConditionalOnMissingBean(IRoleProvider)
    def default_role_provider(self, db_manager, component) -> IRoleProvider:
        return DefaultRoleProvider(db_manager, component)
    
    # 2️⃣ 权限服务（权限判定）
    @Bean
    @ConditionalOnMissingBean(IPermissionService)
    def default_permission_service(self, role_provider) -> IPermissionService:
        return DefaultPermissionService(role_provider)
    
    # 3️⃣ 路径规则提供者（URL权限映射）
    @Bean
    @ConditionalOnMissingBean(IPathPermissionProvider)
    def default_path_permission_provider(self, config_manager) -> IPathPermissionProvider:
        return DefaultPathPermissionProvider(config_manager)
```

---

### 2.3 用户自定义授权（4种方式）

#### 方式1⃣️：自定义IRoleProvider（更换角色来源）

```python
# 场景：从Redis读取角色和权限

from pyspring.security.authorization.contracts.role import IRoleProvider

@Component()
class RedisRoleProvider(IRoleProvider):
    """从Redis读取角色和权限"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get_user_roles(self, user_id):
        """从Redis Set读取用户角色"""
        roles = await self.redis.smembers(f"user:{user_id}:roles")
        return list(roles)
    
    async def get_role_permissions(self, role_name):
        """从Redis Set读取角色权限"""
        perms = await self.redis.smembers(f"role:{role_name}:permissions")
        return list(perms)
    
    async def get_role_hierarchy(self):
        """从Redis Hash读取角色继承关系"""
        hierarchy = await self.redis.hgetall("role:hierarchy")
        # 格式：{"admin": "manager,user", "manager": "user"}
        return {k: v.split(',') for k, v in hierarchy.items()}

# ✅ 效果：DefaultRoleProvider 不会注册，使用 RedisRoleProvider
```

#### 方式2⃣️：集成Casbin（使用企业级RBAC）

```python
# 场景：使用Casbin进行复杂权限判定

import casbin
from pyspring.security.authorization.contracts.permission import IPermissionService

@Component()
class CasbinPermissionService(IPermissionService):
    """使用Casbin进行权限判定"""
    
    def __init__(self):
        self.enforcer = casbin.Enforcer(
            "config/rbac_model.conf",
            "config/rbac_policy.csv"
        )
    
    async def has_permission(self, user_id, permission):
        """Casbin enforce"""
        # Casbin格式：subject, object, action
        # 例如：enforce("user123", "article", "read")
        parts = permission.split(':')
        if len(parts) == 2:
            return self.enforcer.enforce(str(user_id), parts[0], parts[1])
        return False
    
    async def has_role(self, user_id, role):
        """检查用户是否有角色"""
        return self.enforcer.enforce(str(user_id), f"role:{role}", "has")

# ✅ 效果：完全替换权限判定逻辑，使用Casbin的策略引擎

# ⚠️ 可选：添加缓存包装
@Bean()
def cached_casbin_permission_service(
    casbin_service: CasbinPermissionService,
    cache: CacheManagerService
) -> IPermissionService:
    """用缓存装饰Casbin服务"""
    from pyspring.security.authorization.providers.permission.cached import CachedPermissionService
    return CachedPermissionService(
        delegate=casbin_service,
        cache=cache,
        ttl=600  # 10分钟缓存
    )
```

#### 方式3⃣️：自定义权限缓存策略

```python
# 场景：自定义缓存TTL和失效策略

from pyspring.security.authorization.providers.permission.cached import CachedPermissionService

@Bean()
def custom_cached_permission_service(
    default_permission_service: IPermissionService,
    cache: CacheManagerService
) -> IPermissionService:
    """自定义缓存策略"""
    
    class CustomCachedPermissionService(CachedPermissionService):
        def __init__(self, delegate, cache):
            super().__init__(delegate, cache, ttl=1800)  # 30分钟缓存
        
        async def invalidate_user_cache(self, user_id):
            """自定义缓存失效（使用Redis SCAN）"""
            cursor = 0
            while True:
                cursor, keys = await self.cache.scan(
                    cursor,
                    match=f"perm:{user_id}:*",
                    count=100
                )
                if keys:
                    await self.cache.delete(*keys)
                if cursor == 0:
                    break
    
    return CustomCachedPermissionService(default_permission_service, cache)
```

#### 方式4⃣️：自定义IPathPermissionProvider（更换路径规则来源）

```python
# 场景：从数据库动态读取路径权限规则

from pyspring.security.authorization.contracts.rule import IPathPermissionProvider

@Component()
class DatabasePathPermissionProvider(IPathPermissionProvider):
    """从数据库读取路径权限规则"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self._cache = {}
    
    async def load_rules(self):
        """从数据库加载规则"""
        session = await self.db.session()
        result = await session.execute(
            "SELECT path_pattern, required_permissions FROM path_rules"
        )
        self._cache = {
            row.path_pattern: row.required_permissions.split(',')
            for row in result
        }
    
    async def get_required_permissions(self, path: str) -> List[str]:
        """匹配路径的权限要求"""
        for pattern, perms in self._cache.items():
            if self._match_path(path, pattern):
                return perms
        return []

# ✅ 效果：URL权限规则从数据库读取，支持动态更新
```

---

## 三、完整自定义示例

### 示例1：企业级认证（LDAP + SSO）

```python
# custom_security_config.py

from pyspring.ioc.annotations.component import Configuration, Bean

@Configuration
class EnterpriseSecurityConfig:
    """企业级安全配置"""
    
    # 1. 使用LDAP用户提供者
    @Bean()
    def enterprise_user_provider(self, ldap_client) -> IUserProvider:
        return LDAPUserProvider(ldap_client)
    
    # 2. 添加SSO登录支持
    @Bean()
    def sso_login_provider(self, sso_client) -> ILoginProvider:
        return SSOLoginProvider(sso_client)
    
    # 3. 自定义Token生成（JWT + 加密）
    @Bean()
    def secure_token_generator(self, encryption_service) -> ITokenGenerator:
        return EncryptedJWTTokenGenerator(encryption_service)

# ✅ 效果：
# - 用户从LDAP读取
# - 支持密码登录 + SSO登录
# - Token使用加密JWT
```

### 示例2：多租户授权

```python
# multi_tenant_security_config.py

@Configuration
class MultiTenantSecurityConfig:
    """多租户授权配置"""
    
    @Bean()
    def tenant_aware_role_provider(self, db) -> IRoleProvider:
        """租户隔离的角色提供者"""
        
        class TenantRoleProvider(IRoleProvider):
            async def get_user_roles(self, user_id):
                # 从上下文获取租户ID
                tenant_id = get_current_tenant()
                # 查询该租户下的用户角色
                return await db.query(
                    "SELECT role_code FROM user_roles "
                    "WHERE user_id = ? AND tenant_id = ?",
                    user_id, tenant_id
                )
        
        return TenantRoleProvider()
    
    @Bean()
    def tenant_permission_service(self, role_provider) -> IPermissionService:
        """租户隔离的权限服务"""
        return TenantPermissionService(role_provider)

# ✅ 效果：每个租户的角色和权限完全隔离
```

---

## 四、扩展决策树

```
需要扩展什么？
│
├─ 添加新的认证方式（OAuth2、LDAP、短信）？
│   └─ 实现 ILoginProvider → @Component
│
├─ 更换用户存储（Redis、MongoDB）？
│   └─ 实现 IUserProvider → @Component 或 @Bean
│
├─ 更换Token类型（Session、APIKey）？
│   └─ 实现 ITokenGenerator → @Component
│
├─ 更换密码算法（Argon2、PBKDF2）？
│   └─ 实现 IPasswordEncoder → @Component
│
├─ 控制整个登录流程（添加验证码、日志）？
│   └─ 实现 ILoginService → @Bean（替换默认）
│
├─ 更换角色来源（Redis、配置文件）？
│   └─ 实现 IRoleProvider → @Component
│
├─ 集成第三方权限系统（Casbin、OPA）？
│   └─ 实现 IPermissionService → @Component
│
├─ 自定义缓存策略？
│   └─ 继承 CachedPermissionService → @Bean
│
└─ 动态路径规则（数据库、API）？
    └─ 实现 IPathPermissionProvider → @Component
```

---

## 五、最佳实践总结

### ✅ 推荐做法

1. **优先使用@Component**
   ```python
   @Component()  # 简单，自动注册
   class MyCustomProvider(ILoginProvider):
       pass
   ```

2. **需要复杂初始化时使用@Bean**
   ```python
   @Bean()
   def complex_service(...) -> IService:
       service = ComplexService()
       service.configure(...)
       return service
   ```

3. **使用装饰器模式扩展功能**
   ```python
   # 保留默认实现，添加缓存层
   CachedPermissionService(
       delegate=DefaultPermissionService(...),
       cache=cache
   )
   ```

### ⚠️ 注意事项

1. **不要混用**：如果定义了`@Bean`返回`IUserProvider`，就不要再定义`@Component`实现`IUserProvider`

2. **依赖注入顺序**：确保依赖的Bean先注册
   ```python
   # ✅ 正确：IRoleProvider先注册，IPermissionService后注册
   @Bean()
   def my_role_provider() -> IRoleProvider: ...
   
   @Bean()
   def my_permission_service(role_provider: IRoleProvider) -> IPermissionService:
       return MyPermissionService(role_provider)
   ```

3. **测试时可以Mock**：
   ```python
   # 测试环境配置
   @Configuration
   @Profile("test")
   class TestSecurityConfig:
       @Bean()
       def mock_user_provider() -> IUserProvider:
           return MockUserProvider()
   ```

---

## 六、框架优势对比

| 框架 | 默认实现 | 自定义方式 | 侵入性 |
|------|----------|-----------|--------|
| **PySpring Security** | ✅ 完整可用 | @Component/@Bean | 无侵入 |
| Spring Security | ✅ 完整 | @Bean配置 | 无侵入 |
| Django Auth | ✅ 完整 | 继承+配置 | 中等 |
| FastAPI-Users | ⚠️ 需配置 | 类继承 | 较高 |

---

## 总结

PySpring Security通过**@ConditionalOnMissingBean**实现了：

✅ **开箱即用**：默认实现覆盖所有场景  
✅ **无侵入扩展**：实现接口即可，无需修改框架  
✅ **灵活组合**：可以只替换部分组件  
✅ **装饰器友好**：支持装饰器模式增强功能  
✅ **测试友好**：可以轻松Mock组件

**核心理念：框架提供合理的默认实现，用户通过接口自由扩展。**
