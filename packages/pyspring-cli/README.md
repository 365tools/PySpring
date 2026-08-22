# PySpring CLI

Command-line development tools for PySpring Framework.

## Installation

```bash
pip install pyspring-cli
```

## Usage

```bash
# Initialize new project
pyspring init my-project

# Development utilities
pyspring dev init-sync --dynamic
pyspring check --all

# Environment management
pyspring uv setup --dev

# Clean operations
pyspring clean cache
```

## Features

- Project scaffolding and initialization
- Code quality checks (imports, encoding, circular dependencies)
- Development utilities (export sync, template sync)
- UV environment management
- Security key generation

## Documentation

For detailed documentation, visit [PySpring Documentation](https://github.com/eavelabs-community/py-spring)

## Requirements

- Python >= 3.12
- pyspring >= 1.1.0

## License

Apache License 2.0
