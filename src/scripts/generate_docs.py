#!/usr/bin/env python3
"""
Script to generate Sphinx documentation for the NYP FYP CNC Chatbot.
"""

import sys
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

    modules_dir = docs_dir / "modules"

    # Only generate RST files if we're in Docker
    if in_docker:
        # Clean up old RST files before generating new ones
        if modules_dir.exists():
            for f in modules_dir.rglob("*.rst"):
                f.unlink()
        else:
            modules_dir.mkdir(parents=True, exist_ok=True)
    else:
        # On host, just ensure the modules directory exists but don't generate RST files
        if not modules_dir.exists():
            modules_dir.mkdir(parents=True, exist_ok=True)
        print("   Skipping RST file generation on host filesystem")
        return

    # Auto-generate index.rst in Docker
    if in_docker:
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

    # List of source directories to scan (mirror src/ tree)
    source_root = Path("/app/src") if in_docker else Path("src")
    if not source_root.exists():
        print(f"[ERROR] Source root {source_root} does not exist!")
        return

    # Exclude patterns for files we don't want to document
    exclude_patterns = [
        "__init__.py",
        "*.sh",
        "*.bash",
        "*.zsh",
        "*.fish",
        "*.ps1",
        "*.bat",
        "*.cmd",
        "*.exe",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.so",
        "*.dll",
        "*.dylib",
    ]

    def should_exclude_file(file_path):
        filename = file_path.name
        if filename in exclude_patterns:
            return True
        for pattern in exclude_patterns:
            if pattern.startswith("*.") and filename.endswith(pattern[1:]):
                return True
        return False

    def file_to_module(file_path, base_dir):
        rel_path = file_path.relative_to(base_dir)
        parts = rel_path.with_suffix("").parts
        return ".".join(parts)

    def get_automodule_path(file_path, base_dir):
        rel_path = file_path.relative_to(base_dir)
        parts = rel_path.with_suffix("").parts
        return ".".join(parts)

    def get_rst_output_path(file_path, base_dir, modules_dir):
        rel_path = file_path.relative_to(base_dir)
        return modules_dir / rel_path.with_suffix(".rst")

    generated_rst_files = []
    module_to_rst = {}

    print(f"[DEBUG] source_root: {source_root}")
    print(f"[DEBUG] modules_dir: {modules_dir}")

    # Recursively scan all .py files under src/
    for py_file in source_root.rglob("*.py"):
        if should_exclude_file(py_file):
            continue
        module_path = file_to_module(py_file, source_root)
        rst_path = get_rst_output_path(py_file, source_root, modules_dir)
        rst_path.parent.mkdir(parents=True, exist_ok=True)
        module_to_rst[module_path] = rst_path.relative_to(modules_dir).as_posix()
        if not rst_path.exists():
            with open(rst_path, "w", encoding="utf-8") as f:
                if py_file.name == "__init__.py":
                    package_name = py_file.parent.name
                    title = f"{package_name} Package"
                else:
                    title = py_file.stem
                f.write(f"{title}\n")
                f.write(f"{'=' * len(title)}\n\n")
                automodule_path = get_automodule_path(py_file, source_root)
                f.write(f".. automodule:: {automodule_path}\n")
                f.write("   :members:\n")
                f.write("   :undoc-members:\n")
                f.write("   :show-inheritance:\n")
                f.write("   :special-members:\n")
                f.write("   :exclude-members: __weakref__\n")
                if py_file.name == "__init__.py":
                    f.write("   :show-module-summary:\n")
                    f.write("   :imported-members:\n")
            generated_rst_files.append((str(rst_path), automodule_path))
        # Debug: warn if RST file is empty
        if rst_path.stat().st_size == 0:
            print(f"[WARNING] RST file {rst_path} is empty after generation!")

    # Build package indexes and main modules index
    def create_package_indexes(modules_dir, module_to_rst):
        packages = {}
        for module_path, rst_rel_path in module_to_rst.items():
            parts = Path(rst_rel_path).parts
            if len(parts) > 1:
                pkg = parts[0]
                packages.setdefault(pkg, []).append(rst_rel_path)
            # else: skip root-level modules entirely
        # Write index.rst for each package
        for pkg, rst_list in packages.items():
            pkg_dir = modules_dir / pkg
            pkg_dir.mkdir(parents=True, exist_ok=True)
            index_file = pkg_dir / "index.rst"
            with open(index_file, "w") as f:
                f.write(f"{pkg.title()} Package\n")
                f.write(f"{'=' * (len(pkg) + 8)}\n\n")
                f.write(".. toctree::\n")
                f.write("   :maxdepth: 3\n\n")
                for rst_rel in sorted(rst_list):
                    if rst_rel.endswith("__init__.rst"):  # skip __init__
                        continue
                    rel_path = Path(rst_rel).with_suffix("")
                    f.write(f"   {rel_path.relative_to(pkg)}\n")
        # Write main modules.rst (only for packages)
        index_file = modules_dir / "modules.rst"
        with open(index_file, "w") as f:
            f.write("All Modules\n===========\n\n")
            f.write(".. toctree::\n   :maxdepth: 2\n\n")
            for pkg in sorted(packages):
                if (modules_dir / pkg / "index.rst").exists():
                    f.write(f"   {pkg}/index\n")

    create_package_indexes(modules_dir, module_to_rst)

    print("\n✅ RST files generated successfully!")
    print(f"📁 Generated {len(generated_rst_files)} RST files in {modules_dir}")
    print("🏗️ HTML documentation will be built by the calling script")
    return True


if __name__ == "__main__":
    try:
        generate_docs()
    except KeyboardInterrupt:
        print("\n🛑 Received Ctrl+C during documentation generation.")
        print("👋 Shutting down gracefully. Goodbye!")
        sys.exit(0)
