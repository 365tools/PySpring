"""
Template File Synchronization Script

Used to synchronize configuration files from the PySpring root directory to the templates directory.
"""
import shutil
from pathlib import Path

from pyspring.cli.core.ui.console import print_title, print_error, print_info, print_issue, print_summary, print_success


def sync_templates(args):
    """Synchronize template files"""
    current_file = Path(__file__)
    # Resolve root from this file location: src/pyspring/cli/commands/dev/sync.py
    # Root is 6 levels up
    root = current_file.parent.parent.parent.parent.parent.parent

    # If installed as package usage, this might fail to find root if not editable
    if not (root / "pyproject.toml").exists():
        # Fallback try assuming CWD is root
        root = Path.cwd()
        if not (root / "pyproject.toml").exists():
            print_error("Could not search project root. Please run from project root directory.")
            return

    templates_dir = root / "src" / "pyspring" / "templates" / "project"

    # Ensure template directory exists
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Files to sync
    files_to_sync = [
        (".gitignore", ".gitignore.template"),
        ("pyproject.toml", "pyproject.toml.template"),
    ]

    print_title("Syncing Template Files to templates Directory")

    synced_count = 0
    issues_count = 0

    for source_name, target_name in files_to_sync:
        source_path = root / source_name
        target_path = templates_dir / target_name

        if not source_path.exists():
            print_issue("0", f"Source file not found: {source_name}", level='error')
            issues_count += 1
            continue

        # Copy file
        try:
            shutil.copy2(source_path, target_path)

            # Get file size
            size = target_path.stat().st_size
            print_issue("1", f"{source_name} -> {target_name} ({size:,} bytes)", str(target_path), level='success')
            synced_count += 1
        except Exception as e:
            print_issue("0", f"Sync failed: {e}", str(target_path), level='error')
            issues_count += 1

    print_info(f"Template directory: {templates_dir}")
    print_info("Available template files:")
    for file_path in sorted(templates_dir.glob("*")):
        if file_path.is_file():
            print(f"  - {file_path.name}")

    print_summary(issues_count, 0, synced_count, fixable=False)

    if synced_count > 0:
        print()
        print_title("Next Steps")
        print_success("Templates synchronized. You can now:")
        print("  1. Customize templates in 'src/pyspring/templates/project'")
        print("  2. Commit changes to version control")