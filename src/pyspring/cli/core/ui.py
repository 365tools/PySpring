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
        icon = "❌"
        color = Colors.FAIL
    elif level == 'warning':
        icon = "⚠"
        color = Colors.WARNING
    elif level == 'success':
        icon = "✅"
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
