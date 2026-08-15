# PySpring 认证授权架构图

## 完整架构图

```mermaid
graph TB
    subgraph ClientLayer["外部用户层"]
        Client["客户端"]
    end

    subgraph APIGateway["API网关层"]
        Register["POST /auth/register"]
        Login["POST /auth/login"]
        Protected["GET /api/resource"]
        PermRoute["DELETE /api/users/:id"]
        RoleRoute["GET /admin/dashboard"]
    end

    subgraph AuthMiddleware["认证中间层"]
        direction TB
        TokenDep[Token认证依赖 require_authentication_from_token]
        PermDep[权限依赖 permission_dependency]
        RoleDep[角色依赖 role_dependency]
        
        TokenDep --> |验证Token| TokenService
        PermDep --> |1.先认证| TokenDep
        PermDep --> |2.再授权| PermService
        RoleDep --> |1.先认证| TokenDep
        RoleDep --> |2.再授权| PermService
    end

    subgraph CoreService["核心服务层"]
        direction TB
        
        subgraph AuthenticationService["认证服务"]
            AuthService["AuthService"]
            LoginProvider["ILoginProvider"]
            UserProvider["IUserProvider"]
            TokenService["ITokenService"]
            
            AuthService --> LoginProvider
            AuthService --> UserProvider
            AuthService --> TokenService
        end
        
        subgraph AuthorizationService["授权服务"]
            PermService["IPermissionService"]
            RoleProvider["IRoleProvider"]
            
            PermService --> RoleProvider
        end
    end

    subgraph ImplLayer["实现层"]
        direction TB
        
        subgraph TokenImpl["令牌实现"]
            JWTService["JWTTokenService"]
            SessionService["SessionTokenService"]
            APIKeyService["APIKeyTokenService"]
        end
        
        subgraph UserImpl["用户管理实现"]
            DefaultUserMgr["DefaultUserManagerService"]
            CustomUserMgr["CustomUserManagerService"]
        end
        
        subgraph PermImpl["权限实现"]
            DefaultPerm["DefaultPermissionService"]
            CachedPerm["CachedPermissionService"]
        end
        
        subgraph RoleImpl["角色提供者实现"]
            DBRoleProvider["DefaultRoleProvider"]
            ConfigRoleProvider["ConfigRoleProvider"]
        end
        
        TokenService -.实现.-> JWTService
        TokenService -.实现.-> SessionService
        TokenService -.实现.-> APIKeyService
        
        UserProvider -.实现.-> DefaultUserMgr
        UserProvider -.实现.-> CustomUserMgr
        
        PermService -.实现.-> DefaultPerm
        PermService -.实现.-> CachedPerm
        
        RoleProvider -.实现.-> DBRoleProvider
        RoleProvider -.实现.-> ConfigRoleProvider
    end

    subgraph IoCContainer["IoC容器"]
        AppContext["ApplicationContext"]
        
        AppContext -->|"自动注入"| TokenService
        AppContext -->|"自动注入"| UserProvider
        AppContext -->|"自动注入"| PermService
        AppContext -->|"自动注入"| RoleProvider
    end

    subgraph DataLayer["数据层"]
        direction TB
        
        subgraph ORMModels["ORM模型"]
            UserTable[("UserTable")]
            RoleTable[("RoleTable")]
            PermTable[("PermissionTable")]
            UserRoleTable[("UserRoleTable")]
            RolePermTable[("RolePermissionTable")]
        end
        
        subgraph CacheLayer["缓存层"]
            Cache[("Redis/Memcached")]
        end
        
        DefaultUserMgr --> UserTable
        DefaultUserMgr --> UserRoleTable
        
        DBRoleProvider --> RoleTable
        DBRoleProvider --> PermTable
        DBRoleProvider --> RolePermTable
        
        CachedPerm --> Cache
    end

    %% 用户注册流程
    Client -->|"1.注册"| Register
    Register --> AuthService
    AuthService -->|"创建用户"| DefaultUserMgr
    DefaultUserMgr -->|"插入"| UserTable
    DefaultUserMgr -->|"分配角色"| UserRoleTable
    
    %% 用户登录流程
    Client -->|"2.登录"| Login
    Login -->|"查找Provider"| LoginProvider
    LoginProvider -->|"identifier匹配"| UserProvider
    UserProvider -->|"动态字段匹配"| UserTable
    UserProvider -->|"验证密码"| LoginProvider
    LoginProvider -->|"安全验证"| AuthService
    AuthService -->|"验证密码"| DefaultUserMgr
    DefaultUserMgr -->|"查询"| UserTable
    AuthService -->|"生成Token"| JWTService
    JWTService -->|"返回Token"| Client
    
    %% 访问受保护资源
    Client -->|"3.访问资源"| Protected
    Protected --> TokenDep
    TokenDep -->|"验证"| JWTService
    JWTService -->|"解析payload"| TokenDep
    TokenDep -->|"获取用户"| DefaultUserMgr
    DefaultUserMgr -->|"查询"| UserTable
    TokenDep -->|"返回用户"| Protected
    
    %% 访问需要权限的资源
    Client -->|"4.访问"| PermRoute
    PermRoute --> PermDep
    PermDep -->|"has_permission"| DefaultPerm
    DefaultPerm -->|"get_roles"| DBRoleProvider
    DBRoleProvider -->|"查询"| UserRoleTable
    DBRoleProvider -->|"查询"| RolePermTable
    DefaultPerm -->|"检查权限"| PermDep
    PermDep -->|"403或通过"| PermRoute
    
    %% 访问需要角色的资源
    Client -->|"5.访问"| RoleRoute
    RoleRoute --> RoleDep
    RoleDep -->|"has_role"| DefaultPerm
    DefaultPerm -->|"get_roles"| DBRoleProvider
    RoleDep -->|"403或通过"| RoleRoute

    %% 样式定义
    classDef clientStyle fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef apiStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef authStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef serviceStyle fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef implStyle fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef dataStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef iocStyle fill:#e0f2f1,stroke:#004d40,stroke-width:3px
    
    class Client clientStyle
    class Register,Login,Protected,PermRoute,RoleRoute apiStyle
    class TokenDep,PermDep,RoleDep authStyle
    class AuthService,TokenService,UserProvider,PermService,RoleProvider serviceStyle
    class JWTService,SessionService,APIKeyService,DefaultUserMgr,CustomUserMgr,DefaultPerm,CachedPerm,DBRoleProvider,ConfigRoleProvider implStyle
    class UserTable,RoleTable,PermTable,UserRoleTable,RolePermTable,Cache dataStyle
    class AppContext iocStyle
```

## 用户注册流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as POST /auth/register
    participant AuthService as AuthService
    participant UserMgr as IUserManagerService
    participant DB as Database
    
    Client->>API: 注册请求 {username, email, password}
    Note over Client,API: ⚠️ 角色不能由用户指定
    API->>AuthService: register(data)
    AuthService->>AuthService: 验证数据格式
    AuthService->>UserMgr: create_user(user_data)
    UserMgr->>DB: INSERT INTO pyspring_user
    DB-->>UserMgr: user_id
    Note over UserMgr,DB: 🔒 自动分配默认角色
    UserMgr->>DB: INSERT INTO pyspring_user_role (user_id, role_code='guest')
    DB-->>UserMgr: success
    UserMgr-->>AuthService: user_info
    AuthService-->>API: user_created
    API-->>Client: {id, username, email, roles:['guest']}
    Note over API,Client: 新用户只有 'guest' 角色
```

## 用户登录流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as POST /auth/login
    participant AuthService as AuthService
    participant LoginProvider as ILoginProvider
    participant UserProvider as IUserProvider
    participant TokenSvc as ITokenService
    participant DB as Database
    
    Client->>API: 登录请求 {identifier, password}
    Note over Client,API: identifier 可以是: username/email/phone/user_id 由 YAML 配置决定
    API->>AuthService: login(request)
    AuthService->>LoginProvider: supports(request)?
    LoginProvider-->>AuthService: True
    AuthService->>LoginProvider: authenticate(request)
    
    Note over LoginProvider,DB: 根据 identifier_fields 配置匹配
    LoginProvider->>UserProvider: get_user_by_identifier(identifier)
    UserProvider->>DB: SELECT * FROM pyspring_user WHERE email = ? OR username = ? OR user_id = ?
    Note over UserProvider,DB: 动态匹配配置的字段: identifier_fields: [email, username, phone]
    DB-->>UserProvider: user_record
    UserProvider-->>LoginProvider: user_info
    
    LoginProvider->>LoginProvider: verify_password(password, hash)
    alt 密码错误
        LoginProvider-->>AuthService: 401 Unauthorized
        AuthService-->>API: 认证失败
        API-->>Client: {error: "Invalid credentials"}
    else 密码正确
        LoginProvider-->>AuthService: user
        
        Note over AuthService: 安全上下文验证
        AuthService->>AuthService: SecurityContextManager.evaluate()
        alt 违反安全策略
            AuthService-->>API: 403 Forbidden
            API-->>Client: {error: "Security Policy Violation"}
        else 通过验证
            Note over AuthService,TokenSvc: 撤销旧Token
            AuthService->>TokenSvc: revoke_user_refresh_tokens(user_id)
            
            Note over AuthService,TokenSvc: 生成新Token
            AuthService->>TokenSvc: create_access_token({   sub: user_id,   identifier: identifier,   roles: [...] })
            TokenSvc-->>AuthService: access_token
            
            AuthService->>TokenSvc: create_refresh_token(user_id)
            TokenSvc-->>AuthService: refresh_token
            
            AuthService-->>API: {access_token, refresh_token, user_info}
            API-->>Client: {access_token, refresh_token, user_id, username}
        end
    end
```

## Token认证流程（仅认证）

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as GET /api/profile
    participant Dep as require_authentication_from_token
    participant TokenSvc as ITokenService
    participant UserMgr as IUserManagerService
    participant DB as Database
    participant IoC as ApplicationContext
    
    Client->>API: GET /api/profile Authorization: Bearer <token>
    API->>Dep: Depends(require_authentication_from_token)
    Dep->>Dep: 提取 Authorization Header
    Dep->>IoC: get_by_type(ITokenService)
    IoC-->>Dep: token_service
    Dep->>TokenSvc: verify_token(token)
    TokenSvc->>TokenSvc: decode(token, secret)
    alt Token无效/过期
        TokenSvc-->>Dep: raise InvalidToken
        Dep-->>API: 401 Unauthorized
        API-->>Client: {error: "Could not validate credentials"}
    else Token有效
        TokenSvc-->>Dep: payload {sub: user_id, ...}
        Dep->>IoC: get_by_type(IUserManagerService)
        IoC-->>Dep: user_service
        Dep->>UserMgr: get_user_by_id(user_id)
        UserMgr->>DB: SELECT * FROM pyspring_user WHERE id = ?
        DB-->>UserMgr: user_record
        UserMgr-->>Dep: user_info
        Dep-->>API: user (返回用户对象)
        API->>API: 执行业务逻辑
        API-->>Client: {user_id, username, email}
    end
```

## 权限验证流程（认证+授权）

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as DELETE /api/users/:id
    participant PermDep as permission_dependency("user:delete")
    participant AuthDep as require_authentication_from_token
    participant TokenSvc as ITokenService
    participant UserMgr as IUserManagerService
    participant PermSvc as IPermissionService
    participant RoleProv as IRoleProvider
    participant DB as Database
    participant IoC as ApplicationContext
    
    Client->>API: DELETE /api/users/123 Authorization: Bearer <token>
    API->>PermDep: Depends(permission_dependency("user:delete"))
    
    Note over PermDep,AuthDep: 步骤1: Token认证
    PermDep->>AuthDep: Depends(require_authentication_from_token)
    AuthDep->>IoC: get_by_type(ITokenService)
    IoC-->>AuthDep: token_service
    AuthDep->>TokenSvc: verify_token(token)
    TokenSvc-->>AuthDep: payload {sub: user_id}
    AuthDep->>IoC: get_by_type(IUserManagerService)
    IoC-->>AuthDep: user_service
    AuthDep->>UserMgr: get_user_by_id(user_id)
    UserMgr->>DB: SELECT * FROM pyspring_user
    DB-->>UserMgr: user_record
    UserMgr-->>AuthDep: user_info
    AuthDep-->>PermDep: user (已认证用户)
    
    Note over PermDep,RoleProv: 步骤2: 权限检查
    PermDep->>IoC: get_by_type(IPermissionService)
    IoC-->>PermDep: permission_service
    PermDep->>PermSvc: has_permission(user_id, "user:delete")
    PermSvc->>RoleProv: get_effective_roles(user_id)
    RoleProv->>DB: SELECT role_code FROM pyspring_user_role WHERE user_id = ?
    DB-->>RoleProv: ['admin', 'manager']
    RoleProv-->>PermSvc: roles
    
    loop 每个角色
        PermSvc->>RoleProv: get_role_permissions(role)
        RoleProv->>DB: SELECT permission_code FROM pyspring_role_permission WHERE role_code = ?
        DB-->>RoleProv: ['user:*', 'order:read', ...]
        RoleProv-->>PermSvc: permissions
    end
    
    PermSvc->>PermSvc: 检查"user:delete"是否匹配 （精确匹配或通配符）
    
    alt 权限不足
        PermSvc-->>PermDep: False
        PermDep-->>API: 403 Forbidden
        API-->>Client: {error: "Permission denied: user:delete"}
    else 权限通过
        PermSvc-->>PermDep: True
        PermDep-->>API: user (已认证+已授权)
        API->>API: 执行删除逻辑
        API-->>Client: {deleted: 123}
    end
```

## 角色验证流程（认证+授权）

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as GET /admin/dashboard
    participant RoleDep as role_dependency("admin")
    participant AuthDep as require_authentication_from_token
    participant PermSvc as IPermissionService
    participant RoleProv as IRoleProvider
    participant DB as Database
    participant IoC as ApplicationContext
    
    Client->>API: GET /admin/dashboard Authorization: Bearer <token>
    API->>RoleDep: Depends(role_dependency("admin"))
    
    Note over RoleDep,AuthDep: 步骤1: Token认证（同上）
    RoleDep->>AuthDep: 先认证
    AuthDep-->>RoleDep: user (已认证用户)
    
    Note over RoleDep,DB: 步骤2: 角色检查
    RoleDep->>IoC: get_by_type(IPermissionService)
    IoC-->>RoleDep: permission_service
    RoleDep->>PermSvc: has_role(user_id, "admin")
    PermSvc->>RoleProv: get_effective_roles(user_id)
    RoleProv->>DB: SELECT role_code FROM pyspring_user_role WHERE user_id = ?
    DB-->>RoleProv: ['user', 'manager']
    RoleProv-->>PermSvc: roles
    PermSvc->>PermSvc: 检查"admin"是否在角色列表中
    
    alt 角色不足
        PermSvc-->>RoleDep: False
        RoleDep-->>API: 403 Forbidden
        API-->>Client: {error: "Role required: admin"}
    else 角色匹配
        PermSvc-->>RoleDep: True
        RoleDep-->>API: user (已认证+已授权)
        API->>API: 返回仪表板数据
        API-->>Client: {dashboard: {...}}
    end
```

## IoC容器服务注册与发现

```mermaid
graph TB
    subgraph Startup["启动阶段"]
        Start["应用启动"] --> Scanner["包扫描器"]
        Scanner -->|"扫描@Configuration"| Configs["配置类"]
        Scanner -->|"扫描@Component"| Components["组件类"]
        Scanner -->|"扫描@Bean"| Beans["Bean方法"]
    end
    
    subgraph Registration["注册阶段"]
        Configs --> Register["注册到IoC容器"]
        Components --> Register
        Beans --> Register
        
        Register -->|"注册"| AuthConfig["AuthorizationConfiguration"]
        Register -->|"注册"| SecurityConfig["SecurityConfiguration"]
        
        AuthConfig -->|"@Bean"| PermSvcBean["IPermissionService"]
        AuthConfig -->|"@Bean"| RoleProvBean["IRoleProvider"]
        
        SecurityConfig -->|"@Bean"| TokenSvcBean["ITokenService"]
        SecurityConfig -->|"@Bean"| UserSvcBean["IUserManagerService"]
    end
    
    subgraph Runtime["运行时阶段"]
        Request["HTTP请求"] --> Dependency["依赖注入"]
        
        Dependency -->|"调用"| GetByType["ApplicationContext.get_by_type"]
        
        GetByType -->|"获取"| Container["IoC容器"]
        Container -->|"查找"| PermSvcBean
        Container -->|"查找"| RoleProvBean
        Container -->|"查找"| TokenSvcBean
        Container -->|"查找"| UserSvcBean
        
        GetByType -->|"返回实例"| Dependency
        Dependency -->|"注入到"| RouteHandler["路由处理器"]
    end
    
    subgraph Extension["扩展点"]
        Custom["自定义实现"] -->|"实现接口"| ITokenService["ITokenService"]
        Custom -->|"实现接口"| IPermissionService["IPermissionService"]
        Custom -->|"添加@Component"| CustomImpl["自定义组件"]
        
        CustomImpl -->|"自动注册"| Container
        Container -->|"自动使用"| GetByType
    end
    
    classDef startStyle fill:#e3f2fd,stroke:#1565c0
    classDef registerStyle fill:#f3e5f5,stroke:#6a1b9a
    classDef runtimeStyle fill:#e8f5e9,stroke:#2e7d32
    classDef extendStyle fill:#fff3e0,stroke:#e65100
    
    class Start,Scanner,Configs,Components,Beans startStyle
    class Register,AuthConfig,SecurityConfig,PermSvcBean,RoleProvBean,TokenSvcBean,UserSvcBean registerStyle
    class Request,Dependency,GetByType,Container,RouteHandler runtimeStyle
    class Custom,ITokenService,IPermissionService,CustomImpl extendStyle
```

## 数据库ER图

```mermaid
erDiagram
    USER ||--o{ USER_ROLE : "has"
    ROLE ||--o{ USER_ROLE : "assigned_to"
    ROLE ||--o{ ROLE_PERMISSION : "has"
    PERMISSION ||--o{ ROLE_PERMISSION : "granted_to"
    
    USER {
        int id
        string username
        string email
        string password_hash
        boolean active
        string created_at
        string updated_at
    }
    
    ROLE {
        int id
        string code
        string name
        string description
        string created_at
    }
    
    PERMISSION {
        int id
        string code
        string name
        string resource
        string action
        string created_at
    }
    
    USER_ROLE {
        int id
        int user_id
        string role_code
        string assigned_at
    }
    
    ROLE_PERMISSION {
        int id
        string role_code
        string permission_code
        string granted_at
    }
```

### 数据示例

**USER表**：

- id: 主键（PK）
- username, email: 唯一键（UK）

**ROLE表**：

- id: 主键（PK）
- code: 唯一键（UK），值如 `admin`, `manager`, `guest`
- name: `管理员`, `经理`, `访客`

**PERMISSION表**：

- id: 主键（PK）
- code: 唯一键（UK），值如 `user:read`, `user:write`, `order:delete`
- resource: `user`, `order`
- action: `read`, `write`, `delete`

**USER_ROLE表**：

- id: 主键（PK）
- user_id: 外键（FK）→ USER.id
- role_code: 外键（FK）→ ROLE.code

**ROLE_PERMISSION表**：

- id: 主键（PK）
- role_code: 外键（FK）→ ROLE.code
- permission_code: 外键（FK）→ PERMISSION.code

## 可扩展性架构

```mermaid
graph LR
    subgraph "接口层 (Interface Layer)"
        IToken[ITokenService 令牌服务接口]
        IUser[IUserManagerService 用户管理接口]
        IPerm[IPermissionService 权限服务接口]
        IRole[IRoleProvider 角色提供者接口]
    end
    
    subgraph "默认实现 (Default Implementation)"
        JWT[JWTTokenService JWT实现]
        DefaultUser[DefaultUserManagerService 数据库用户]
        DefaultPerm[DefaultPermissionService RBAC权限]
        DBRole[DefaultRoleProvider 数据库角色]
    end
    
    subgraph "扩展实现1 (Extension 1 - OAuth)"
        OAuth[OAuthTokenService OAuth2.0实现]
        OAuthUser[OAuthUserManagerService 第三方用户]
    end
    
    subgraph "扩展实现2 (Extension 2 - LDAP)"
        LDAP[LDAPTokenService LDAP认证]
        LDAPUser[LDAPUserManagerService LDAP用户]
        LDAPRole[LDAPRoleProvider LDAP角色]
    end
    
    subgraph "扩展实现3 (Extension 3 - Cache)"
        CachedPerm[CachedPermissionService 缓存权限]
        RedisCache[RedisCache Redis缓存]
    end
    
    subgraph "扩展实现4 (Extension 4 - Multi-Tenant)"
        TenantToken[TenantTokenService 多租户Token]
        TenantUser[TenantUserManagerService 租户用户]
        TenantPerm[TenantPermissionService 租户权限]
    end
    
    IToken -.实现.-> JWT
    IToken -.扩展.-> OAuth
    IToken -.扩展.-> LDAP
    IToken -.扩展.-> TenantToken
    
    IUser -.实现.-> DefaultUser
    IUser -.扩展.-> OAuthUser
    IUser -.扩展.-> LDAPUser
    IUser -.扩展.-> TenantUser
    
    IPerm -.实现.-> DefaultPerm
    IPerm -.扩展.-> CachedPerm
    IPerm -.扩展.-> TenantPerm
    
    IRole -.实现.-> DBRole
    IRole -.扩展.-> LDAPRole
    
    CachedPerm --> RedisCache
    
    classDef interfaceStyle fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    classDef defaultStyle fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef extendStyle fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class IToken,IUser,IPerm,IRole interfaceStyle
    class JWT,DefaultUser,DefaultPerm,DBRole defaultStyle
    class OAuth,OAuthUser,LDAP,LDAPUser,LDAPRole,CachedPerm,RedisCache,TenantToken,TenantUser,TenantPerm extendStyle
```

## 认证授权决策树

```mermaid
graph TD
    Start[HTTP请求] --> HasToken{是否携带Token?}
    
    HasToken -->|否| PublicRoute{是否公开路由?}
    PublicRoute -->|是| Allow[允许访问]
    PublicRoute -->|否| Deny401[401 Unauthorized 需要认证]
    
    HasToken -->|是| VerifyToken[验证Token]
    VerifyToken --> TokenValid{Token有效?}
    
    TokenValid -->|否| Deny401
    TokenValid -->|是| GetUser[获取用户信息]
    
    GetUser --> UserActive{用户激活?}
    UserActive -->|否| Deny403User[403 Forbidden 用户已禁用]
    UserActive -->|是| CheckAuthz{需要授权?}
    
    CheckAuthz -->|否| Allow
    CheckAuthz -->|是| AuthzType{授权类型?}
    
    AuthzType -->|权限| CheckPerm[检查权限]
    AuthzType -->|角色| CheckRole[检查角色]
    
    CheckPerm --> HasPerm{拥有权限?}
    HasPerm -->|是| Allow
    HasPerm -->|否| Deny403Perm[403 Forbidden 权限不足]
    
    CheckRole --> HasRole{拥有角色?}
    HasRole -->|是| Allow
    HasRole -->|否| Deny403Role[403 Forbidden 角色不足]
    
    classDef successStyle fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef errorStyle fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef processStyle fill:#bbdefb,stroke:#1565c0,stroke-width:2px
    classDef decisionStyle fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class Allow successStyle
    class Deny401,Deny403User,Deny403Perm,Deny403Role errorStyle
    class VerifyToken,GetUser,CheckPerm,CheckRole processStyle
    class HasToken,PublicRoute,TokenValid,UserActive,CheckAuthz,AuthzType,HasPerm,HasRole decisionStyle
```

## 架构特点总结

### 🎯 核心特性

1. **分层架构**
    - API网关层：路由定义
    - 认证中间层：Token验证、权限检查
    - 核心服务层：业务逻辑接口
    - 实现层：具体实现
    - 数据层：数据库、缓存

2. **接口驱动**
    - ITokenService：令牌服务接口
    - IUserManagerService：用户管理接口
    - IPermissionService：权限服务接口
    - IRoleProvider：角色提供者接口

3. **IoC容器**
    - 自动服务发现
    - 依赖注入
    - 单例管理

4. **可扩展性**
    - JWT/OAuth/LDAP/多租户令牌
    - 数据库/LDAP角色提供者
    - 默认/缓存权限服务
    - 自定义实现无缝集成

5. **安全性**
    - Token认证
    - 权限控制（RBAC）
    - 角色控制
    - 通配符权限

### 🔐 认证流程

```
注册（默认guest角色）→ 登录 → 获取Token → 携带Token访问 → 验证Token → 检查权限/角色 → 访问资源
```

### 🛡️ 安全机制

1. **注册安全**
    - 新用户默认分配 `guest` 角色
    - 角色不能在注册时指定（防止权限提升攻击）
    - 管理员角色需通过管理后台授予

2. **Token安全**
    - JWT签名验证
    - Token过期检查
    - 用户状态验证（是否被禁用）

3. **权限控制**
    - RBAC（基于角色的访问控制）
    - 支持通配符权限（`user:*`）
    - 角色继承机制

### ⚡ 性能优化

- 权限缓存（CachedPermissionService）
- 角色继承
- Token缓存
- 数据库查询优化
