import os
import re

target_dir = r"d:\Project\PycharmProjects\PySpring"


def fix_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to match pyspring.security.authentication not followed by a letter (to avoid matching authorization or authentication)
        # We look for pyspring.security.authentication where the next char is NOT a word char (a-z, A-Z, 0-9, _)
        # Actually simplest is just (?![a-zA-Z]) since we are worried about suffixes.
        pattern = r"pyspring\.security\.auth(?![a-zA-Z])"

        if re.search(pattern, content):
            new_content = re.sub(pattern, "pyspring.security.authentication", content)
            if content != new_content:
                print(f"Fixing {filepath}")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")


for root, dirs, files in os.walk(target_dir):
    if "node_modules" in root or ".git" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            fix_file(os.path.join(root, file))
