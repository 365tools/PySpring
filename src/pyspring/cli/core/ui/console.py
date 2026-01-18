"""
PySpring CLI Console Utilities
"""


class Colors:
    """Terminal Colors"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    YELLOW = '\033[93m'
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
    # Simply print file path, maybe bold?
    print(f"\n{Colors.BOLD}📄 {file_path}{Colors.ENDC}")


def print_issue(line: str, message: str, file_path: str = None, level: str = 'error'):
    """
    Print standard issue format
    Level: 'error', 'warning', 'success', 'info'
    """
    if level == 'error':
        icon = "✗"
        color = Colors.FAIL
    elif level == 'warning':
        icon = "⚠"
        color = Colors.YELLOW
    elif level == 'success':
        icon = "✓"
        color = Colors.OKGREEN
    else:  # info
        icon = "ℹ"
        color = Colors.OKCYAN

    # Format: Icon  Message   Location
    # We pad message to align locations somewhat, but not strictly to avoid huge gaps

    location = f"{file_path}:{line}" if file_path else f"Line {line}"

    # Clean output: [Icon] [Location] Message
    # This puts the clickable link at the start (some terminals like this) 
    # OR at the end. VSCode likes "path:line: ... " or " ... path:line"

    # Try a standard linter format optimized for readability
    #   ✗ path/to/file.py:10: Module not found
    
    if file_path:
        print(f"  {color}{icon} {file_path}:{line}{Colors.ENDC} {message}")
    else:
        print(f"  {color}{icon} Line {line}: {message}{Colors.ENDC}")


def print_fix(file_path: str, line: int, message: str, action: str = "Fixed"):
    """
    Print a fix action result
    """
    print(f"  {Colors.OKGREEN}🛠  {file_path}:{line}{Colors.ENDC} {action}: {message}")


def print_standard_import_tips(missing_imports: bool = True):
    """
    Print standard diagnostic tips for import-related checks.
    """
    print_section("Troubleshooting & Next Steps")

    if missing_imports:
        print(f"{Colors.YELLOW}Diagnostic Tips for Missing Imports:{Colors.ENDC}")
        print("1. Ensure you have activated the correct virtual environment")
        print("2. Install missing dependencies: run `uv sync` or `pip install -r requirements.txt`")
        print("3. For local modules, ensure the project root or 'src' is in PYTHONPATH")
        print("")

    print(f"{Colors.OKCYAN}For detailed analysis, run the following diagnostic commands:{Colors.ENDC}\n")

    commands = [
        ("pyspring check diagnose", "Verify environment integrity and package installation"),
        ("pyspring check imports-circular", "Detect circular import dependencies"),
        ("pyspring check references", "Identify and fix unresolved symbol references"),
        ("pyspring check imports-explicit", "Refactor ambiguous imports to explicit submodules"),
    ]

    for cmd, desc in commands:
        print(f"  {Colors.BOLD}{cmd:<35}{Colors.ENDC} : {desc}")

    print(f"\n{Colors.OKCYAN}Tip: Use '--fix' with supported commands to apply automated corrections.{Colors.ENDC}")



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
