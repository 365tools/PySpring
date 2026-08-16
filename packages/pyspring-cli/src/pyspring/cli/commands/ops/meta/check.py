import importlib
import inspect
import pkgutil
from typing import List, Type

from pyspring.cli.core.commands.base import BaseCommand, CommandArg
from pyspring.cli.core.ui.console import (
    Colors,
    print_error,
    print_section,
    print_success,
    print_title,
)
from pyspring.cli.core.utils.logging import suppress_logs


class CliCheckCommand(BaseCommand):
    name = "check"
    help = "Verify CLI command structure and integrity"
    description = "Dynamically scans and validates all registered CLI commands, args, and subcommands."

    def run(self, args):
        check_cli_structure()


def check_cli_structure(package_path: str = 'pyspring.cli.commands'):
    """
    Dynamically discover and validate all CLI commands in the given package.
    Prints a hierarchical tree of commands and verifies their integrity.
    """
    print_title("CLI Integrity Check & Registry")

    try:
        # Import the package to get its path
        package = importlib.import_module(package_path)
    except ImportError as e:
        print_error(f"Failed to import commands package '{package_path}': {e}")
        return

    found_commands = []
    errors = []

    # 1. Discovery Phase
    print(f"{Colors.BOLD}Scanning package: {package_path}...{Colors.ENDC}\n")

    # Suppress logs during import to avoid noise from module-level initialization
    with suppress_logs(patterns=[r'.*']):
        for _, name, _ in pkgutil.iter_modules(package.__path__):
            if name.startswith('_'):
                continue

            full_module_name = f"{package_path}.{name}"
            try:
                module = importlib.import_module(full_module_name)

                # Find BaseCommand subclasses defined in this module
                module_commands = []
                for _, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BaseCommand) and obj is not BaseCommand:
                        if obj.__module__ == module.__name__:
                            module_commands.append(obj)

                if not module_commands:
                    # Warning: Module exists but no BaseCommand found (might be utility or legacy)
                    # We can skip warning if it's strictly enforced, but for now just ignore
                    pass
                else:
                    found_commands.extend(module_commands)

            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                errors.append(f"Module '{name}' failed to load: {e}\n{Colors.FAIL}{tb}{Colors.ENDC}")

    # 2. Validation & Tree Printing Phase
    print_section("Command Hierarchy")

    # Filter out commands that are already subcommands of others
    all_subcommands = set()
    for cmd in found_commands:
        subs = getattr(cmd, 'subcommands', []) or []
        for sub in subs:
            all_subcommands.add(sub)

    # Root commands are those not referenced as subcommands
    root_commands = [c for c in found_commands if c not in all_subcommands]

    sorted_commands = sorted(root_commands, key=lambda x: x.name or '')
    count = len(sorted_commands)

    for i, cmd_class in enumerate(sorted_commands):
        is_last = (i == count - 1)
        _validate_and_print_command(cmd_class, errors, prefix="", is_last=is_last)

    # 3. Summary
    print("\n" + "-" * 70)
    if errors:
        print_error(f"Found {len(errors)} issues during CLI check:")
        for err in errors:
            print(f"  - {err}")
    else:
        print_success(f"Successfully verified {len(found_commands)} top-level commands.")
        print_success("All commands loaded and structure is valid.")


def _validate_and_print_command(cmd_class: Type[BaseCommand], errors: List[str], prefix: str = "", is_last: bool = True):
    """Recursively validate and print command tree with ASCII lines"""

    # ├── if middle item, └── if last item
    connector = "└── " if is_last else "├── "

    # Validation Checks
    cmd_name = getattr(cmd_class, 'name', None)
    if not cmd_name:
        errors.append(f"Class '{cmd_class.__name__}' is missing 'name' attribute")
        display_name = f"{Colors.FAIL}<Missing Name>{Colors.ENDC}"
    else:
        display_name = f"{Colors.OKGREEN}{cmd_name}{Colors.ENDC}"

    help_text = getattr(cmd_class, 'help', "No help provided")

    # Print Command Line
    # Root level usually doesn't need indentation if it's the very first text,
    # but here we follow the tree structure.
    print(f"{prefix}{connector}{display_name} : {help_text}")

    # Prepare prefix for next level
    # If this was the last item, children don't need the vertical bar │
    child_prefix = prefix + ("    " if is_last else "│   ")

    # Validate Arguments
    args: List[CommandArg] = getattr(cmd_class, 'arguments', [])
    if args:
        arg_list = []
        for arg in args:
            flags = arg.flags if isinstance(arg.flags, list) else [arg.flags]
            flags_str = ", ".join(flags)
            arg_list.append(f"{flags_str}")

        # Print args somewhat connected to the tree
        print(f"{child_prefix}· {Colors.OKCYAN}[args]: {', '.join(arg_list)}{Colors.ENDC}")

    # Check Subcommands
    subcommands = getattr(cmd_class, 'subcommands', [])
    if subcommands:
        # Sort subcommands by name for consistent tree output
        # Assuming subcommands have a 'name' attribute or we sort by class name
        try:
            # Try to sort by 'name' attribute, fallback to class name
            subcommands = sorted(subcommands, key=lambda x: getattr(x, 'name', x.__name__))
        except Exception:
            # Fallback if something is weird
            pass

        count = len(subcommands)
        for i, sub_cmd in enumerate(subcommands):
            if not issubclass(sub_cmd, BaseCommand):
                errors.append(f"Command '{cmd_name}' has invalid subcommand '{sub_cmd}'")
                continue

            is_last_sub = (i == count - 1)
            _validate_and_print_command(sub_cmd, errors, prefix=child_prefix, is_last=is_last_sub)
