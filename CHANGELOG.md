# Changelog

All notable changes to PySpring will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-12-24

### Added

**IoC Container & Dependency Injection**

- IoC (Inversion of Control) container with automatic dependency resolution
- Singleton service lifecycle management through `ISingletonService` interface
- Type-based and name-based injection strategies
- Thread-safe lazy initialization
- Automatic service scanning and registration

**Application Lifecycle Management**

- `IStartupInitializer` interface for extensible startup tasks
- `StartupInitializerManager` for centralized initialization orchestration
- `IShutdownHandler` interface for graceful resource cleanup
- Automatic initializer and handler discovery

**Database Auto-Initialization**

- `DatabaseInitializer` for automatic schema creation on application startup
- Incremental mode: safely creates missing tables only
- Full mode: complete schema recreation (development only)
- Intelligent SQL script path detection (scripts/db/, scripts/, db/)
- Configuration-driven via `repositories.yaml`

**Security & Authentication**

- RBAC (Role-Based Access Control) authorization system
- JWT authentication with token encryption (Fernet/AES-GCM algorithms)
- Authentication chain using Chain of Responsibility pattern
- Multi-device authentication and tracking
- Flexible whitelist configuration (exact match, prefix, regex)
- Token auto-renewal mechanism

**Data Access Layer**

- Unified cache abstraction with transparent Memory/Redis switching
- Multi-database support (PostgreSQL, SQLite)
- Automatic connection pool management
- Database and cache connection lifecycle management
- Failover mechanisms for degraded service mode

**Logging Infrastructure**

- Structured logging system based on Loguru
- Colored console output for enhanced development experience
- Automatic log rotation (size and time-based)
- JSON format support for log aggregation
- Contextual request tracking and filtering

**Project Scaffolding**

- `pyspring init` CLI command for project initialization
- Standardized project structure generation (app/, config/, scripts/, tests/, logs/, data/)
- Template-based code generation system
- Automatic JWT key generation
- Environment variable template creation
- SQL script generation from SQLAlchemy models

**Configuration Management**

- YAML-based configuration system
- Environment variable interpolation
- Configuration validation and type checking
- Centralized configuration for all framework components
- Hot-reload support for development

**CLI Tools**

- `pyspring init` - Initialize new project with standard structure
- `pyspring diagnose` - Diagnostic tool for installation verification
- Template synchronization tool (`tools/sync_templates.py`)
- Encryption key generator

### Changed

- Migrated from `requirements.txt` to `pyproject.toml` for modern Python packaging
- Unified all configuration templates under `src/pyspring/templates/`
- Reorganized documentation into six logical categories
- Optimized database initializer error handling and logging

### Fixed

- Thread-safety issues in singleton service creation
- Connection pool cleanup on application shutdown
- Environment variable parsing for complex YAML configurations
- SQL script path detection edge cases

### Documentation

**New Documentation Structure**

- [01-getting-started/](docs/01-getting-started/) - Installation and quick start
- [02-core-concepts/](docs/02-core-concepts/) - IoC container and architecture
- [03-configuration/](docs/03-configuration/) - Configuration system
- [04-features/](docs/04-features/) - Feature modules
- [05-advanced/](docs/05-advanced/) - Advanced topics
- [06-troubleshooting/](docs/06-troubleshooting/) - Problem solving

**Key Documentation**

- Installation Guide - Detailed setup instructions
- Quick Reference - Command and configuration cheatsheet
- IoC Container Guide - Dependency injection patterns
- Security Configuration - Authentication and authorization setup
- JWT Encryption Guide - Token encryption implementation
- Database Auto-Init - Automatic schema management
- Template Management - Customizing code generation

### Technical Details

**Dependencies**

- FastAPI >= 0.104.0
- SQLAlchemy >= 2.0.0
- Loguru >= 0.7.0
- Pydantic >= 2.0.0
- Redis >= 5.0.0
- Cryptography >= 41.0.0

**Python Version**

- Requires Python 3.12+

**Package Structure**

```
pyspring/
├── core/           # Core framework components
├── ioc/            # IoC container
├── security/       # Authentication and authorization
├── repositories/   # Data access layer
├── log/            # Logging system
├── system/         # Configuration management
└── templates/      # Code generation templates
```

---

## Release Notes

### What's New in 1.0.0

PySpring 1.0.0 is the initial stable release of the framework. This version provides a complete, production-ready infrastructure for building enterprise Python web applications with Spring Boot-inspired architecture.

**Highlights:**

- Complete IoC container with dependency injection
- Production-ready authentication and authorization
- Automatic database schema initialization
- Unified data access abstraction
- Professional logging infrastructure
- Comprehensive documentation

**Getting Started:**

```bash
pip install pyspring
pyspring init
```

**Migration from Pre-release:**
If you were using pre-release versions, please refer to the [Migration Guide](docs/05-advanced/SECURITY_MIGRATION_GUIDE.md).

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](#contributing) for details.

- **Bug Reports**: [GitHub Issues](https://github.com/365tools/PySpring/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/365tools/PySpring/discussions)
- **Pull Requests**: [GitHub Pull Requests](https://github.com/365tools/PySpring/pulls)

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Links

- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)
- **GitHub**: https://github.com/365tools/PySpring
- **PyPI**: https://pypi.org/project/pyspring/

---

*For older releases and detailed version history, see [GitHub Releases](https://github.com/365tools/PySpring/releases).*
