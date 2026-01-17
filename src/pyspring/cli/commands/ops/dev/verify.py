"""Verify generated pyproject.toml content"""
import shutil
import tempfile
from pathlib import Path

from pyspring.cli.core.ui import print_title, print_section, print_error
# Correct import path assuming internal usage
from ..init_ops.core import create_pyproject_toml


def verify_pyproject(args):
    """Verify pyproject.toml generation logic"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        create_pyproject_toml(temp_dir)

        pyproject_path = temp_dir / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text(encoding='utf-8')

            print_title("Verified pyproject.toml Content")
            print(content)
            print_section("End of Content")
        else:
            print_error("Failed to generate pyproject.toml")
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
