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

    # Use /app/docs if it exists (Docker), otherwise use local workspace docs
    docker_docs_dir = Path("/app/docs")
    local_docs_dir = Path(__file__).parent.parent / "docs"
    if docker_docs_dir.exists():
        docs_dir = docker_docs_dir
    else:
        docs_dir = local_docs_dir

    modules_dir = docs_dir / "modules"
    # Clean up old RST files before generating new ones
    if modules_dir.exists():
        for f in modules_dir.glob("*.rst"):
            f.unlink()
    else:
        modules_dir.mkdir(parents=True, exist_ok=True)

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

    # Helper to convert file path to Python module path (relative to /app, not app.)
    def file_to_module(file_path, base_dir):
        rel_path = file_path.relative_to(base_dir)
        parts = rel_path.with_suffix("").parts
        return ".".join(parts)

    # Helper to convert module path to unique RST filename
    def module_to_rst_name(module_path):
        # Use the original filename (case-sensitive) for RST filename
        return module_path.replace(".", "_") + ".rst"

    # Scan for all .py files in each source directory
    generated_rst_files = []  # Track all generated RST files for debugging
    module_to_rst = {}  # Map module path to rst filename
    for label, src in source_dirs:
        src_path = docs_dir.parent / src
        if not src_path.exists():
            print(f"[DEBUG] Source path does not exist: {src_path}")
            continue
        for py_file in src_path.rglob("*.py"):
            # Skip __init__.py for now (optional: document packages if desired)
            if py_file.name == "__init__.py":
                continue
            module_path = file_to_module(py_file, docs_dir.parent)
            rst_name = module_to_rst_name(module_path)
            rst_path = modules_dir / rst_name
            module_to_rst[module_path] = rst_name
            if not rst_path.exists():
                # Write default RST
                with open(rst_path, "w", encoding="utf-8") as f:
                    # Use the exact filename (case-sensitive) for the title
                    f.write(f"{py_file.stem}\n")
                    f.write(f"{'=' * len(py_file.stem)}\n\n")
                    f.write(f".. automodule:: {module_path}\n")
                    f.write("   :members:\n")
                    f.write("   :undoc-members:\n")
                    f.write("   :show-inheritance:\n")
                print(f"[DEBUG] Generated RST: {rst_path} for module {module_path}")
                generated_rst_files.append((str(rst_path), module_path))
            else:
                print(
                    f"[DEBUG] RST already exists: {rst_path} for module {module_path}"
                )
                generated_rst_files.append((str(rst_path), module_path))

    # After scanning all source_dirs, ensure app.py and flexcyon_theme.py are included
    for special_file in ["app.py", "flexcyon_theme.py"]:
        special_path = docs_dir.parent / special_file
        if special_path.exists():
            module_path = file_to_module(special_path, docs_dir.parent)
            rst_name = module_to_rst_name(module_path)
            rst_path = modules_dir / rst_name
            module_to_rst[module_path] = rst_name
            if not rst_path.exists():
                with open(rst_path, "w", encoding="utf-8") as f:
                    # Use the exact filename (case-sensitive) for the title
                    f.write(f"{special_path.stem}\n")
                    f.write(f"{'=' * len(special_path.stem)}\n\n")
                    f.write(f".. automodule:: {module_path}\n")
                    f.write("   :members:\n")
                    f.write("   :undoc-members:\n")
                    f.write("   :show-inheritance:\n")
                print(f"[DEBUG] Generated RST: {rst_path} for module {module_path}")
                generated_rst_files.append((str(rst_path), module_path))
            else:
                print(
                    f"[DEBUG] RST already exists: {rst_path} for module {module_path}"
                )
                generated_rst_files.append((str(rst_path), module_path))

    # When generating RST for root-level modules, ensure automodule uses just the module name
    for py_file in docs_dir.parent.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        module_path = py_file.stem  # Just the filename without .py
        rst_name = module_to_rst_name(module_path)
        rst_path = modules_dir / rst_name
        module_to_rst[module_path] = rst_name
        if not rst_path.exists():
            with open(rst_path, "w", encoding="utf-8") as f:
                # Use the exact filename (case-sensitive) for the title
                f.write(f"{py_file.stem}\n")
                f.write(f"{'=' * len(py_file.stem)}\n\n")
                f.write(f".. automodule:: {module_path}\n")
                f.write("   :members:\n")
                f.write("   :undoc-members:\n")
                f.write("   :show-inheritance:\n\n")

    # Rebuild package indexes to only reference existing RSTs
    create_package_indexes(modules_dir, module_to_rst)
    fix_rst_titles(modules_dir)
    cleanup_duplicate_titles(modules_dir)

    # Print summary of all generated RST files
    print("\n[DEBUG] Summary of all RST files generated or found:")
    for rst_path, module_path in generated_rst_files:
        try:
            size = Path(rst_path).stat().st_size
            print(f"  - {rst_path} (module: {module_path}, size: {size} bytes)")
            if size == 0:
                print(f"[WARNING] RST file is empty: {rst_path}")
            else:
                with open(rst_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if ".. automodule::" not in content:
                        print(
                            f"[WARNING] RST file missing automodule directive: {rst_path}"
                        )
        except Exception as e:
            print(f"[ERROR] Could not stat or read {rst_path}: {e}")
    print(f"[DEBUG] Total RST files: {len(generated_rst_files)}\n")

    # Build HTML documentation
    print("🏗️ Building HTML documentation...")
    try:
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
                str(docs_dir),
                str(docs_dir / "_build/html"),
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Sphinx build failed: {e}")
        raise
    print("✅ Sphinx documentation generated successfully!")
    print("📖 Documentation available at: /app/docs/_build/html/index.html")


def create_package_indexes(modules_dir, module_to_rst):
    """
    Create package index files to organize modules properly.

    This function creates RST index files for each package to organize
    the generated documentation in a hierarchical structure.
    """
    # Define package structure with more comprehensive module patterns
    # Dynamically detect all root-level .py files (except __init__.py)
    root_py_files = [
        f.stem
        for f in (modules_dir.parent.parent).glob("*.py")
        if f.name != "__init__.py"
    ]
    packages = {
        "backend": ["backend."],
        "gradio_modules": ["gradio_modules."],
        "llm": ["llm."],
        "infra_utils": ["infra_utils."],
        "scripts": ["scripts."],
        "tests": ["tests."],
        "documentation": ["docs."],
        "root": root_py_files,
    }

    fix_rst_titles(modules_dir)

    included_modules = set()
    for package_name, module_prefixes in packages.items():
        index_file = modules_dir / f"{package_name}.rst"
        with open(index_file, "w") as f:
            f.write(f"{package_name.replace('_', ' ').title()}\n")
            f.write("=" * len(package_name) + "\n\n")
            f.write(".. toctree::\n")
            f.write("   :maxdepth: 6\n")
            f.write("   :caption: Modules:\n\n")
            # Add modules that match the prefixes, but only if not already included
            for module_path, rst_name in sorted(module_to_rst.items()):
                if module_path in included_modules:
                    continue
                for prefix in module_prefixes:
                    if module_path == prefix or module_path.startswith(prefix):
                        f.write(f"   {rst_name[:-4]}\n")
                        included_modules.add(module_path)
                        break
            # Add a section for the package itself if it exists as a module
            if package_name in module_to_rst:
                f.write(f"\n.. automodule:: {package_name}\n")
                f.write("   :members:\n")
                f.write("   :undoc-members:\n")
                f.write("   :show-inheritance:\n")
    create_main_modules_index(modules_dir)


def fix_rst_titles(modules_dir: Path) -> None:
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


def cleanup_duplicate_titles(modules_dir: Path) -> None:
    """
    Clean up duplicate titles and ensure proper documentation organization.
    """
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


def create_main_modules_index(modules_dir: Path) -> None:
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
