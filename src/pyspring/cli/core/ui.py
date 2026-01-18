"""
PySpring CLI UI Utilities
"""


class Colors:
    """Terminal Colors"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print section divider"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_header(text: str):
    """Print header with formatting"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_title(text: str):
    """Print standard command title"""
    print_header(text)


def print_file_header(file_path: str):
    """Print standard file header"""
    print(f"{Colors.OKCYAN}ℹ File: {file_path}{Colors.ENDC}")


def print_issue(line: str, message: str, file_path: str = None, level: str = 'error'):
    """
    Print standard issue format
    Level: 'error', 'warning', 'success', 'info'
    """
    if level == 'error':
        icon = "✗"  # Changed from ❌ for consistency
        color = Colors.FAIL
    elif level == 'warning':
        icon = "⚠"
        color = Colors.WARNING
    elif level == 'success':
        icon = "✓"  # Changed from ✅ for consistency
        color = Colors.OKGREEN
    else:  # info
        icon = "ℹ"
        color = Colors.OKCYAN

    location_suffix = ""
    if file_path:
        # Standardize clickable link (VSCode/PyCharm compatible: path:line)
        # Assuming line is convertible to str
        location_suffix = f" -> {file_path}:{line}"

    print(f"  {color}{icon} Line {line}: {message}{Colors.ENDC}{location_suffix}")


def print_summary(total_issues: int, files_count: int = 0, fixed_count: int = 0, fixable: bool = False):
    """Print standard summary footer"""
    print_section("Summary")
    files_info = f" in {files_count} files" if files_count > 0 else ""
    
    if total_issues == 0:
        print_success(f"No issues found{files_info}.")
    else:
        print(f"Found {total_issues} issues{files_info}.")
        if fixed_count > 0:
            print_success(f"Fixed {fixed_count} issues.")
        elif fixable:
            print_info("Run with --fix to apply automated fixes.")


def print_standard_command_help(
        title: str,
        description: str,
        usage: list[tuple[str, str]],
        options: list[tuple[str, str]] = None,
        subcommands: dict[str, str] = None,
        checks: list[tuple[str, bool]] = None,
        tips: list[str] = None
):
    """
    Print a standardized help interface for any CLI command.
    """
    if title:
        print_title(title)

    if description:
        print(f"\n{description}")

    # 1. Environment Checks (if provided)
    if checks:
        print(f"\n{Colors.BOLD}[Environment Check]{Colors.ENDC}")
        for msg, passed in checks:
            if passed:
                print(f"  {Colors.OKGREEN}✓ {msg}{Colors.ENDC}")
            else:
                print(f"  {Colors.FAIL}✗ {msg}{Colors.ENDC}")

    # 2. Usage Section
    if usage:
        print(f"\n{Colors.BOLD}[Usage]{Colors.ENDC}")
        max_len = max(len(u[0]) for u in usage) if usage else 0
        for cmd, desc in usage:
            print(f"  {Colors.OKBLUE}{cmd:<{max_len}}{Colors.ENDC} : {desc}")

    # 3. Subcommands Section (if provided)
    if subcommands:
        print(f"\n{Colors.BOLD}[Available Commands]{Colors.ENDC}")
        max_len = max(len(k) for k in subcommands.keys()) if subcommands else 0
        for name, desc in sorted(subcommands.items()):
            print(f"  {Colors.OKCYAN}➜ {name:<{max_len}}{Colors.ENDC} : {desc}")

    # 4. Options Section (if provided)
    if options:
        print(f"\n{Colors.BOLD}[Options]{Colors.ENDC}")
        max_len = max(len(o[0]) for o in options) if options else 0
        for flag, desc in options:
            print(f"  {Colors.OKCYAN}{flag:<{max_len}}{Colors.ENDC} : {desc}")

    # 5. Tips/Warnings
    if tips:
        print()
        for tip in tips:
            print(f"{Colors.WARNING}💡 Tip: {tip}{Colors.ENDC}")


def print_check_summary(results: list[tuple[str, bool]], fix_commands: dict[str, str]):
    """
    Print a summary table of check results and actionable fixes.
    
    Args:
        results: List of (check_name, passed_boolean)
        fix_commands: Dict of {check_name: fix_command_suffix}
                      e.g. {'encoding': '--fix'}
                      If check name not in dict, assumes manual fix.
    """
    print_section("CHECK SUMMARY")

    all_passed = True
    for name, success in results:
        status = f"{Colors.OKGREEN}✅ PASS{Colors.ENDC}" if success else f"{Colors.FAIL}❌ ISSUES{Colors.ENDC}"
        if not success: all_passed = False
        print(f"{name:<20} : {status}")

    print("-" * 70)

    if all_passed:
        print_success("All checks passed! Project is healthy.")
    else:
        print_warning("Some checks found issues.")

        print(f"\n{Colors.BOLD}[Action Required]{Colors.ENDC}")
        for name, success in results:
            if not success:
                print(f"\n  • {name} found issues:")
                print(f"      Check: pyspring check {name}")

                if name in fix_commands:
                    fix_suffix = fix_commands[name]
                    print(f"      Fix:   pyspring check {name} {fix_suffix}")
                else:
                    print(f"      Fix:   Manual resolution required")

    # Add final separator for clean UI
    print()
    print("-" * 70)
