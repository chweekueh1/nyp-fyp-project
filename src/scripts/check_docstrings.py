#!/usr/bin/env python3
"""
Script to check for missing top-level module docstrings in all Python files in the project.

- Recursively scans from the project root (excluding virtual environments and __init__.py files).
- Prints a list of files missing a top-level docstring.
- Exits with code 1 if any are missing, 0 otherwise.
- Supports optional --max-depth argument to limit recursion depth (default: unlimited).
"""

import os
import sys
import ast
import argparse

EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "node_modules",
    ".nypai-chatbot",
}


def has_top_level_docstring(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
        return ast.get_docstring(tree) is not None
    except Exception as e:
        print(f"[ERROR] Could not parse {filepath}: {e}")
        return False


def find_py_files(root, max_depth=None):
    root_depth = root.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(root):
        # Exclude unwanted directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        if max_depth is not None:
            current_depth = dirpath.rstrip(os.sep).count(os.sep) - root_depth
            if current_depth >= max_depth:
                dirnames[:] = []  # Don't recurse further
        for filename in filenames:
            if filename.endswith(".py") and filename != "__init__.py":
                yield os.path.join(dirpath, filename)


def main():
    parser = argparse.ArgumentParser(
        description="Check for missing top-level docstrings in Python files."
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Maximum recursion depth (default: unlimited)",
    )
    args = parser.parse_args()

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    missing = []
    for pyfile in find_py_files(project_root, max_depth=args.max_depth):
        if not has_top_level_docstring(pyfile):
            missing.append(pyfile)
    if missing:
        print(
            "\n❌ The following Python files are missing a top-level module docstring:"
        )
        for f in missing:
            print(f"  - {os.path.relpath(f, project_root)}")
        print(f"\nTotal: {len(missing)} file(s) missing docstrings.")
        sys.exit(1)
    else:
        print("\n✅ All Python files have a top-level module docstring!")
        sys.exit(0)


if __name__ == "__main__":
    main()
