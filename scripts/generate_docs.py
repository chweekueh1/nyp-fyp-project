#!/usr/bin/env python3
"""
Script to generate Sphinx documentation for the NYP FYP CNC Chatbot.
"""

import sys
from pathlib import Path


def generate_docs():
    """
    Generate Sphinx documentation by scanning source directories and generating RST files for each module.
    Only generates RST files when running in Docker container, not on the host filesystem.
    """
    print("🔍 Generating Sphinx documentation...")

    # Use /app/docs if it exists (Docker), otherwise use local workspace docs
    docker_docs_dir = Path("/app/docs")
    local_docs_dir = Path(__file__).parent.parent / "docs"

    # Check if we're running in Docker - look for /app directory and Docker environment
    in_docker = docker_docs_dir.exists() and Path("/app").exists()

    if in_docker:
        docs_dir = docker_docs_dir
        print("🐳 Running in Docker container - RST files will be generated")
        print(f"[DEBUG] Docker docs dir: {docker_docs_dir}")
        print(f"[DEBUG] Docker docs dir exists: {docker_docs_dir.exists()}")
        print(f"[DEBUG] /app directory exists: {Path('/app').exists()}")
        print(f"[DEBUG] Current working directory: {Path.cwd()}")
        print(f"[DEBUG] /app contents: {list(Path('/app').iterdir())}")
        print(f"[DEBUG] /app/docs contents: {list(Path('/app/docs').iterdir())}")
    else:
        docs_dir = local_docs_dir
        print("🖥️  Running on host filesystem - RST files will NOT be generated")
        print(
            "   RST files are only generated within Docker containers to avoid polluting the host filesystem"
        )

    modules_dir = docs_dir / "modules"

    # Only generate RST files if we're in Docker
    if in_docker:
        # Clean up old RST files before generating new ones
        if modules_dir.exists():
            for f in modules_dir.glob("*.rst"):
                f.unlink()
        else:
            modules_dir.mkdir(parents=True, exist_ok=True)
    else:
        # On host, just ensure the modules directory exists but don't generate RST files
        if not modules_dir.exists():
            modules_dir.mkdir(parents=True, exist_ok=True)
        print("   Skipping RST file generation on host filesystem")

    # List of source directories to scan
    source_dirs = [
        ("backend", "backend"),
        ("gradio_modules", "gradio_modules"),
        ("llm", "llm"),
        ("infra_utils", "infra_utils"),
        ("scripts", "scripts"),
        ("tests", "tests"),
        ("docs", "docs"),
    ]

    # Files to exclude from documentation generation
    exclude_patterns = [
        "__init__.py",
        "*.sh",  # Shell scripts
        "*.bash",  # Bash scripts
        "*.zsh",  # Zsh scripts
        "*.fish",  # Fish scripts
        "*.ps1",  # PowerShell scripts
        "*.bat",  # Batch files
        "*.cmd",  # Command files
        "*.exe",  # Executables
        "*.pyc",  # Compiled Python
        "*.pyo",  # Optimized Python
        "*.pyd",  # Python DLLs
        "*.so",  # Shared objects
        "*.dll",  # Dynamic link libraries
        "*.dylib",  # macOS dynamic libraries
    ]

    # Root-level Python files to include in documentation
    root_modules = [
        "app.py",
        "system_prompts.py",
        "hashing.py",
        "performance_utils.py",
        "setup.py",
        "flexcyon_theme.py",
    ]

    def should_exclude_file(file_path):
        """Check if a file should be excluded from documentation."""
        filename = file_path.name

        # Check exact filename matches
        if filename in exclude_patterns:
            return True

        # Check pattern matches
        for pattern in exclude_patterns:
            if pattern.startswith("*."):
                if filename.endswith(pattern[1:]):
                    return True

        return False

    # Helper to convert file path to Python module path (relative to /app, not app.)
    def file_to_module(file_path, base_dir):
        rel_path = file_path.relative_to(base_dir)
        parts = rel_path.with_suffix("").parts
        return ".".join(parts)

    # Helper to convert module path to unique RST filename
    def module_to_rst_name(module_path):
        # Use the original filename (case-sensitive) for RST filename
        # Handle special cases like llm.dataProcessing -> llm_dataProcessing
        return module_path.replace(".", "_") + ".rst"

    # Helper to get the correct module path for automodule directive
    def get_automodule_path(file_path, base_dir):
        """Get the correct module path for the automodule directive."""
        rel_path = file_path.relative_to(base_dir)
        parts = rel_path.with_suffix("").parts
        module_path = ".".join(parts)

        # For root-level files, use just the filename without .py
        if len(parts) == 1:
            return parts[0]

        return module_path

    # Helper to check if a module should be included in documentation
    def should_include_module(module_path: str) -> bool:
        """Check if a module should be included in documentation."""
        # Include __init__.py files as they often contain important package documentation
        # Skip test files that don't have meaningful docstrings
        if module_path.startswith("tests.") and "test_" in module_path:
            # Only include test files that have proper docstrings
            return True

        return True

    # Only scan and generate RST files if we're in Docker
    generated_rst_files = []  # Track all generated RST files for debugging
    module_to_rst = {}  # Map module path to rst filename

    if in_docker:
        # First, handle root-level modules
        for root_file in root_modules:
            root_path = docs_dir.parent / root_file
            if root_path.exists():
                module_path = root_file.replace(".py", "")  # Remove .py extension
                rst_name = module_to_rst_name(module_path)
                rst_path = modules_dir / rst_name
                module_to_rst[module_path] = rst_name

                with open(rst_path, "w", encoding="utf-8") as f:
                    # Use the exact filename (case-sensitive) for the title
                    title = root_path.stem
                    f.write(f"{title}\n")
                    f.write(f"{'=' * len(title)}\n\n")
                    # Use the correct module path for automodule
                    automodule_path = module_path
                    f.write(f".. automodule:: {automodule_path}\n")
                    f.write("   :members:\n")
                    f.write("   :undoc-members:\n")
                    f.write("   :show-inheritance:\n")
                print(f"[DEBUG] Generated RST: {rst_path} for module {automodule_path}")
                generated_rst_files.append((str(rst_path), automodule_path))

        # Scan for all .py files in each source directory
        for label, src in source_dirs:
            src_path = docs_dir.parent / src
            if not src_path.exists():
                print(f"[DEBUG] Source path does not exist: {src_path}")
                continue
            for py_file in src_path.rglob("*.py"):
                # Skip excluded files
                if should_exclude_file(py_file):
                    print(f"[DEBUG] Excluding file: {py_file}")
                    continue

                module_path = file_to_module(py_file, docs_dir.parent)
                rst_name = module_to_rst_name(module_path)
                rst_path = modules_dir / rst_name
                module_to_rst[module_path] = rst_name

                # Check if module should be included
                if not should_include_module(module_path):
                    print(f"[DEBUG] Skipping module: {module_path}")
                    continue

                if not rst_path.exists():
                    # Write default RST
                    with open(rst_path, "w", encoding="utf-8") as f:
                        # Generate appropriate title
                        if py_file.name == "__init__.py":
                            # For __init__.py files, use the package name
                            package_name = py_file.parent.name
                            title = f"{package_name} Package"
                        else:
                            # Use the exact filename (case-sensitive) for the title
                            title = py_file.stem

                        f.write(f"{title}\n")
                        f.write(f"{'=' * len(title)}\n\n")
                        # Use the correct module path for automodule
                        automodule_path = get_automodule_path(py_file, docs_dir.parent)
                        f.write(f".. automodule:: {automodule_path}\n")
                        f.write("   :members:\n")
                        f.write("   :undoc-members:\n")
                        f.write("   :show-inheritance:\n")
                        f.write("   :special-members:\n")
                        f.write("   :exclude-members: __weakref__\n")

                        # Special handling for __init__.py files
                        if py_file.name == "__init__.py":
                            f.write("   :show-module-summary:\n")
                            f.write("   :imported-members:\n")
                    print(
                        f"[DEBUG] Generated RST: {rst_path} for module {automodule_path}"
                    )
                    generated_rst_files.append((str(rst_path), automodule_path))
                else:
                    print(
                        f"[DEBUG] RST already exists: {rst_path} for module {automodule_path}"
                    )
                    generated_rst_files.append((str(rst_path), automodule_path))

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
                print(f"[ERROR] Error processing {rst_path}: {e}")

        print(f"\n[DEBUG] Total RST files: {len(generated_rst_files)}")

    # RST files have been generated successfully
    print("\n✅ RST files generated successfully!")
    print(f"📁 Generated {len(generated_rst_files)} RST files in {modules_dir}")
    print("🏗️ HTML documentation will be built by the calling script")

    return True


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

    # Create a more robust package structure
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

    # Ensure all package directories exist and have __init__.py files
    for package_name in [
        "backend",
        "gradio_modules",
        "llm",
        "infra_utils",
        "scripts",
        "tests",
        "docs",
    ]:
        package_dir = modules_dir.parent.parent / package_name
        if package_dir.exists() and not (package_dir / "__init__.py").exists():
            print(f"[WARNING] Missing __init__.py in {package_name} directory")

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
            package_modules = []
            for module_path, rst_name in sorted(module_to_rst.items()):
                if module_path in included_modules:
                    continue
                for prefix in module_prefixes:
                    if module_path == prefix or module_path.startswith(prefix):
                        # Include all modules including __init__.py files
                        package_modules.append((module_path, rst_name))
                        included_modules.add(module_path)
                        break

            # Write the package modules
            for module_path, rst_name in package_modules:
                f.write(f"   {rst_name[:-4]}\n")

            # Add a section for the package itself if it exists as a module
            if package_name in module_to_rst:
                f.write(f"\n.. automodule:: {package_name}\n")
                f.write("   :members:\n")
                f.write("   :undoc-members:\n")
                f.write("   :show-inheritance:\n")

    # Debug: Print what was included in each package
    print("\n[DEBUG] Package index summary:")
    for package_name, module_prefixes in packages.items():
        included_count = sum(
            1
            for module_path in module_to_rst.keys()
            if any(
                module_path == prefix or module_path.startswith(prefix)
                for prefix in module_prefixes
            )
        )
        print(f"  - {package_name}: {included_count} modules")

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
