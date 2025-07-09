#!/usr/bin/env python3
"""
Script to generate Sphinx documentation for the NYP FYP CNC Chatbot.
"""

import subprocess
import sys
from pathlib import Path


def generate_docs():
    """
    Generate Sphinx documentation by scanning source directories and generating RST files for each module.
    """
    print("🔍 Generating Sphinx documentation...")

    docs_dir = Path("/app/docs")
    modules_dir = docs_dir / "modules"
    modules_dir.mkdir(exist_ok=True)

    # List of source directories to scan
    source_dirs = [
        ("backend", "backend"),
        ("gradio_modules", "gradio_modules"),
        ("llm", "llm"),
        ("infra_utils", "infra_utils"),
        ("scripts", "scripts"),
        ("tests", "tests"),
        ("docs", "docs"),
        (".", "."),  # root-level modules
    ]

    # Helper to convert file path to Python module path
    def file_to_module(file_path, base_dir):
        rel_path = file_path.relative_to(base_dir.parent)
        parts = rel_path.with_suffix("").parts
        return ".".join(parts)

    # Scan for all .py files in each source directory
    for label, src in source_dirs:
        src_path = docs_dir.parent / src
        if not src_path.exists():
            continue
        for py_file in src_path.rglob("*.py"):
            # Skip __init__.py for now (optional: document packages if desired)
            if py_file.name == "__init__.py":
                continue
            module_path = file_to_module(py_file, docs_dir.parent)
            rst_name = f"{py_file.stem}.rst"
            rst_path = modules_dir / rst_name
            if not rst_path.exists():
                # Write default RST
                with open(rst_path, "w", encoding="utf-8") as f:
                    f.write(f"{py_file.stem.replace('_', ' ').title()}\n")
                    f.write(f"{'=' * len(py_file.stem)}\n\n")
                    f.write(f".. automodule:: {module_path}\n")
                    f.write("   :members:\n")
                    f.write("   :undoc-members:\n")
                    f.write("   :show-inheritance:\n")

    # Rebuild package indexes to only reference existing RSTs
    create_package_indexes()
    fix_rst_titles(modules_dir)
    cleanup_duplicate_titles()

    # Build HTML documentation
    print("🏗️ Building HTML documentation...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-b",
            "html",
            "-D",
            "napoleon_google_docstring=True",
            "-D",
            "napoleon_numpy_docstring=True",
            "-D",
            "autodoc_docstring_signature=1",
            "-D",
            "autodoc_preserve_defaults=1",
            "-D",
            "autodoc_inherit_docstrings=1",
            "-D",
            "autodoc_show_inheritance=1",
            "-D",
            "autodoc_show_sourcelink=1",
            ".",
            "_build/html",
        ],
        check=True,
    )
    print("✅ Sphinx documentation generated successfully!")
    print("📖 Documentation available at: /app/docs/_build/html/index.html")


def create_package_indexes():
    """
    Create package index files to organize modules properly.

    This function creates RST index files for each package to organize
    the generated documentation in a hierarchical structure.
    """
    modules_dir = Path("modules")

    # Define package structure with more comprehensive module patterns
    packages = {
        "backend": ["backend.*"],
        "gradio_modules": [
            "audio_input",
            "change_password",
            "chatbot",
            "classification_formatter",
            "enhanced_content_extraction",
            "file_classification",
            "file_upload",
            "login_and_register",
            "search_interface",
        ],
        "llm": ["chatModel", "classificationModel", "dataProcessing", "keyword_cache"],
        "infra_utils": ["infra_utils", "infra_utils.*"],
        "scripts": [
            "bootstrap_tests",
            "check_env",
            "debug_search_integration",
            "docker_cleanup",
            "docker_utils",
            "entrypoint",
            "env_utils",
            "fix_permissions",
            "generate_docs",
            "main",
            "test_utils",
            "serve_docs",
        ],
        "tests": [
            "test_*",
            "comprehensive_test_suite",
            "run_*",
            "verify_organization",
            "demo_*",
        ],
        "documentation": [
            "docs",  # Only the main docs module
        ],
        "root": [
            "app",
            "setup",
            "system_prompts",
            "performance_utils",
            "hashing",
            "flexcyon_theme",
            "infra_utils",
        ],
    }

    # Fix RST files to ensure they have proper titles
    fix_rst_titles(modules_dir)

    for package_name, module_patterns in packages.items():
        index_file = modules_dir / f"{package_name}.rst"

        with open(index_file, "w") as f:
            f.write(f"{package_name.replace('_', ' ').title()}\n")
            f.write("=" * len(package_name) + "\n\n")

            f.write(".. toctree::\n")
            f.write("   :maxdepth: 6\n")  # Increased maxdepth
            f.write("   :caption: Modules:\n\n")

            # Add modules that match the patterns
            for rst_file in sorted(modules_dir.glob("*.rst")):
                if rst_file.name == f"{package_name}.rst":
                    continue

                module_name = rst_file.stem
                include_module = False

                for pattern in module_patterns:
                    if pattern.endswith("*"):
                        prefix = pattern[:-1]
                        if module_name.startswith(prefix):
                            include_module = True
                            break
                    elif module_name == pattern:
                        include_module = True
                        break

                if include_module:
                    f.write(f"   {module_name}\n")

            # Add a section for the package itself if it exists as a module
            if (modules_dir / f"{package_name}.rst").exists():
                f.write(f"\n.. automodule:: {package_name}\n")
                f.write("   :members:\n")
                f.write("   :undoc-members:\n")
                f.write("   :show-inheritance:\n")

    # Create a main modules index
    create_main_modules_index(modules_dir)


def fix_rst_titles(modules_dir: Path):
    """
    Fix RST files to ensure they have proper titles and remove duplicates.

    :param modules_dir: Path to the modules directory containing RST files.
    :type modules_dir: Path
    """
    for rst_file in modules_dir.glob("*.rst"):
        if rst_file.name in ["index.rst", "modules.rst"]:
            continue

        try:
            with open(rst_file, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")

            # Check if file already has a proper title (starts with a word and has underline)
            has_title = False
            if len(lines) >= 2:
                first_line = lines[0].strip()
                second_line = lines[1].strip()

                # Check if first line is a title and second line is an underline
                if (
                    first_line
                    and not first_line.startswith("#")
                    and not first_line.startswith("..")
                    and second_line
                    and all(
                        c == "=" or c == "-" or c == "*" or c == "^"
                        for c in second_line
                    )
                    and len(second_line) >= len(first_line) * 0.8
                ):
                    has_title = True

            if not has_title:
                # Add a proper title
                module_name = rst_file.stem
                title = module_name.replace("_", " ").title()

                # Skip if the title would be the same as the filename
                if title.lower() != module_name.lower():
                    # Create new content with title
                    new_content = f"{title}\n{'=' * len(title)}\n\n{content}"

                    with open(rst_file, "w", encoding="utf-8") as f:
                        f.write(new_content)

        except Exception as e:
            print(f"Warning: Could not fix title for {rst_file}: {e}")


def cleanup_duplicate_titles():
    """
    Clean up duplicate titles and ensure proper documentation organization.
    """
    modules_dir = Path("modules")

    # Remove duplicate RST files that might have been created
    processed_files = set()

    for rst_file in modules_dir.glob("*.rst"):
        if rst_file.name in ["index.rst", "modules.rst"]:
            continue

        # Check for duplicate content
        try:
            with open(rst_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Create a hash of the content to detect duplicates
            content_hash = hash(content.strip())

            if content_hash in processed_files:
                # This is a duplicate, remove it
                rst_file.unlink()
                print(f"   - Removed duplicate: {rst_file.name}")
            else:
                processed_files.add(content_hash)

        except Exception as e:
            print(f"Warning: Could not process {rst_file}: {e}")


def create_main_modules_index(modules_dir: Path):
    """
    Create a main modules index file to organize all modules.

    :param modules_dir: Path to the modules directory.
    :type modules_dir: Path
    """
    index_file = modules_dir / "modules.rst"

    with open(index_file, "w") as f:
        f.write("All Modules\n")
        f.write("===========\n\n")

        f.write(".. toctree::\n")
        f.write("   :maxdepth: 6\n")
        f.write("   :caption: All Modules:\n\n")

        # Add all package index files
        package_files = [
            "backend",
            "gradio_modules",
            "llm",
            "infra_utils",
            "scripts",
            "tests",
            "documentation",
            "root",
        ]

        for package in package_files:
            if (modules_dir / f"{package}.rst").exists():
                f.write(f"   {package}\n")


if __name__ == "__main__":
    import signal

    def signal_handler(signum, frame):
        """Handle graceful shutdown on SIGTERM/SIGINT"""
        print("\n🛑 Received shutdown signal during documentation generation.")
        print("👋 Shutting down gracefully. Goodbye!")
        sys.exit(0)

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        generate_docs()
    except KeyboardInterrupt:
        print("\n🛑 Received Ctrl+C during documentation generation.")
        print("👋 Shutting down gracefully. Goodbye!")
        sys.exit(0)
