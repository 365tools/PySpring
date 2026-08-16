"""
Reporting Utilities
"""
from typing import Dict, List, Tuple

from .console import Colors, print_section, print_success, print_warning


def print_check_summary(results: List[Tuple[str, bool]], fix_commands: Dict[str, str]):
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
                    print("      Fix:   Manual resolution required")

    # Add final separator for clean UI
    print()
    print("-" * 70)
