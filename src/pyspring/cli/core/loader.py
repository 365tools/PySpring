import importlib
import logging
import pkgutil


def load_commands(subparsers, package_path='pyspring.cli.commands'):
    """
    Dynamically loads command modules from the specified package path
    and calls their register_subcommand method.

    Args:
        subparsers: The argparse subparsers object to register commands to.
        package_path: The dot-notation path to the commands package.
    """
    try:
        # Import the package to get its filesystem path
        package = importlib.import_module(package_path)
    except ImportError as e:
        logging.error(f"Failed to import commands package '{package_path}': {e}")
        return

    # Iterate through all modules in the package
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
        # specific skip rules
        if name.startswith('_') or name.endswith('_ops'):
            continue

        full_module_name = f"{package_path}.{name}"

        try:
            module = importlib.import_module(full_module_name)

            # Check if the module has the registration hook
            if hasattr(module, 'register_subcommand'):
                module.register_subcommand(subparsers)
            # else:
            #     # Optional: logging.debug(f"Module {name} has no register_subcommand")
            #     pass

        except Exception as e:
            logging.warning(f"Error loading command '{name}': {e}")
