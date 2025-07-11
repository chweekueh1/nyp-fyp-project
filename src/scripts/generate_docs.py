#!/usr/bin/env python3
"""
Script to generate Sphinx documentation for the NYP FYP CNC Chatbot.
"""

import sys
import subprocess
from pathlib import Path


def generate_docs():
    print("🔍 Generating Sphinx documentation...")

    # Use /app/docs if it exists (Docker), otherwise use local workspace docs
    docker_docs_dir = Path("/app/docs")
    local_docs_dir = Path(__file__).parent.parent / "docs"
    in_docker = docker_docs_dir.exists() and Path("/app").exists()

    if in_docker:
        docs_dir = docker_docs_dir
        print("🐳 Running in Docker container - RST files will be generated")
    else:
        docs_dir = local_docs_dir
        print("🖥️  Running on host filesystem - RST files will NOT be generated")
        print(
            "   RST files are only generated within Docker containers to avoid polluting the host filesystem"
        )
        return

    modules_dir = docs_dir / "modules"

    # Clean up old RST files before generating new ones
    if modules_dir.exists():
        for f in modules_dir.rglob("*.rst"):
            f.unlink()
    else:
        modules_dir.mkdir(parents=True, exist_ok=True)

    # Auto-generate index.rst
    index_rst = docs_dir / "index.rst"
    index_content = """.. AUTO-GENERATED INDEX.RST -- DO NOT EDIT MANUALLY

Welcome to NYP FYP CNC Chatbot's documentation!
==================================================

.. toctree::
   :maxdepth: 6
   :caption: Contents:
   :glob:

   modules/*

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
"""
    with open(index_rst, "w", encoding="utf-8") as f:
        f.write(index_content)
    print(f"[generate_docs.py] Auto-generated index.rst at {index_rst}")

    # List of source directories to scan
    source_root = Path("/app/src") if in_docker else Path("src")
    if not source_root.exists():
        print(f"[ERROR] Source root {source_root} does not exist!")
        return

    # Use sphinx-apidoc to generate RST files
    try:
        # Build sphinx-apidoc command
        cmd = [
            "sphinx-apidoc",
            "-o",
            str(modules_dir),
            "--separate",
            "--module-first",
            "--maxdepth=6",
            "--private",
            "--no-headings",
            str(source_root / "backend"),
            str(source_root / "gradio_modules"),
            str(source_root / "llm"),
            str(source_root / "infra_utils"),
            str(source_root / "scripts"),
            str(source_root / "tests"),
            str(source_root / "misc"),
            str(source_root),
        ]

        print(f"[generate_docs.py] Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(docs_dir))

        if result.returncode == 0:
            print("✅ sphinx-apidoc completed successfully")
            if result.stdout:
                print(f"Output: {result.stdout}")
        else:
            print(f"❌ sphinx-apidoc failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Error running sphinx-apidoc: {e}")
        return False

    # Add missing docstring message to generated RST files
    add_missing_docstring_messages(modules_dir)

    print("\n✅ RST files generated successfully!")
    print(f"📁 Generated RST files in {modules_dir}")
    print("🏗️ HTML documentation will be built by the calling script")
    return True


def add_missing_docstring_messages(modules_dir: Path):
    """Add missing docstring messages to RST files."""
    missing_docstring_msg = """
.. note::

   **Missing Documentation Notice**

   If you do not see documentation on this page, check the Sphinx build logic or if the file has an appropriate docstring.

   This could be due to:

   * Missing or incomplete docstrings in the source code
   * Import errors during documentation generation
   * Syntax errors in the source files
   * Missing dependencies during build

   Please ensure all public functions, classes, and modules have proper docstrings following Google or Sphinx style.
"""

    for rst_file in modules_dir.rglob("*.rst"):
        try:
            with open(rst_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if the file has any actual content beyond the automodule directive
            if ".. automodule::" in content and not any(
                section in content.lower()
                for section in [
                    "arguments:",
                    "parameters:",
                    "returns:",
                    "raises:",
                    "examples:",
                ]
            ):
                # Add missing docstring message
                with open(rst_file, "w", encoding="utf-8") as f:
                    f.write(content + missing_docstring_msg)

        except Exception as e:
            print(f"Warning: Could not process {rst_file}: {e}")


if __name__ == "__main__":
    try:
        generate_docs()
    except KeyboardInterrupt:
        print("\n🛑 Received Ctrl+C during documentation generation.")
        print("👋 Shutting down gracefully. Goodbye!")
        sys.exit(0)
