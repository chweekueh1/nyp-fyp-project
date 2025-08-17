# (no code)
"""
Script to generate and serve Sphinx documentation for the project.
"""

import subprocess
import sys
import os


def build_docs(docs_dir, build_dir):
    """Build the Sphinx documentation for the project.

    Generates HTML documentation from the source files in the specified docs directory and outputs them to the build directory.

    Args:
        docs_dir (str): The directory containing the Sphinx documentation source files.
        build_dir (str): The directory where the built HTML documentation will be placed.
    """
    print(f"Generating Sphinx documentation in {build_dir} ...")
    result = subprocess.run(
        [sys.executable, "-m", "sphinx", "-b", "html", docs_dir, build_dir]
    )
    if result.returncode == 0:
        print("✅ Documentation generated successfully.")
    else:
        print("❌ Documentation generation failed.")
        sys.exit(result.returncode)


def serve_docs(build_dir, port=8080):
    """Serve the generated Sphinx documentation using a simple HTTP server.

    Starts an HTTP server in the specified build directory on the given port. This allows users to view the generated documentation in their browser.

    Args:
        build_dir (str): The directory containing the built HTML documentation.
        port (int, optional): The port to serve the documentation on. Defaults to 8080.
    """
    import http.server
    import socketserver

    os.chdir(build_dir)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"🌐 Serving docs at http://0.0.0.0:{port} (Ctrl+C to stop)")
        httpd.serve_forever()


def main():
    """Generate and serve the Sphinx documentation for the project.

    This function checks for required documentation files, generates API .rst files, builds the HTML documentation, and serves it via a local HTTP server.
    """
    docs_dir = os.path.dirname(os.path.abspath(__file__))  # /app/docs
    build_dir = os.path.join(docs_dir, "_build")

    conf_py = os.path.join(docs_dir, "conf.py")
    index_rst = os.path.join(docs_dir, "index.rst")
    makefile = os.path.join(docs_dir, "Makefile")
    if not os.path.exists(conf_py):
        print(f"❌ conf.py not found in {docs_dir}. Cannot build docs.")
        sys.exit(1)
    if not os.path.exists(index_rst):
        print(
            f"❌ index.rst not found in {docs_dir}. Sphinx needs an index.rst as the master document."
        )
        sys.exit(1)
    if not os.path.exists(makefile):
        print(
            f"❌ Makefile not found in {docs_dir}. Sphinx needs a Makefile to build docs."
        )
        sys.exit(1)

    # Generate .rst files for your modules using sphinx-apidoc via Makefile
    print("Running: make apidoc")
    result = subprocess.run(["make", "apidoc"], cwd=docs_dir)
    if result.returncode != 0:
        print("❌ make apidoc failed.")
        sys.exit(result.returncode)

    os.makedirs(build_dir, exist_ok=True)
    build_docs(docs_dir, build_dir)
    # Serve the docs
    serve_docs(build_dir, port=8080)


if __name__ == "__main__":
    main()
