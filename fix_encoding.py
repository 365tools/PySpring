from pathlib import Path

# Fix container.py
Path('src/pyspring/ioc/container.py').write_text(
    "from pyspring.ioc.core.container import Container, DynamicContainer\n__all__ = ['Container', 'DynamicContainer']",
    encoding='utf-8'
)

# Fix validator.py
Path('src/pyspring/ioc/validator.py').write_text(
    "from pyspring.ioc.core.validator import IoCValidator\n__all__ = ['IoCValidator']",
    encoding='utf-8'
)

print("Files fixed.")
