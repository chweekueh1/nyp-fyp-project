#!/bin/sh
set -e

# Set documentation mode to prevent test execution during doc generation
export DOCUMENTATION=1

# Function to handle graceful shutdown
cleanup() {
    echo ""
    echo "[serve_docs.sh] Received shutdown signal. Cleaning up..."
    echo "[serve_docs.sh] Documentation server shutting down gracefully."
    exit 0
}

# Set up signal handlers for graceful shutdown
trap cleanup SIGTERM SIGINT

echo ""
echo "=== [serve_docs.sh] Starting documentation build and serve process ==="
echo ""

# Check if we're running in Docker
if [ -d "/app/docs" ]; then
    echo "[serve_docs.sh] 🐳 Running in Docker container"
    echo "[serve_docs.sh] RST files will be generated automatically"
else
    echo "[serve_docs.sh] 🖥️  Running on host filesystem"
    echo "[serve_docs.sh] RST files will NOT be generated (only in Docker containers)"
fi

# Generate RST files and build HTML documentation with detailed progress
echo ""
echo "[serve_docs.sh] Step 1: Generating RST files..."
echo "[serve_docs.sh] This may take a few minutes on first run..."

# Run the documentation generation script (ONLY call to generate_docs.py)
# The script will automatically detect Docker vs host and handle RST generation accordingly
/home/appuser/.nypai-chatbot/venv-docs/bin/python /app/generate_docs.py

echo ""
echo "[serve_docs.sh] Step 2: Building HTML documentation..."
echo "[serve_docs.sh] This may take a few minutes..."

# Build the HTML documentation
cd /app/docs
/home/appuser/.nypai-chatbot/venv-docs/bin/sphinx-build \
    -b html \
    -D napoleon_google_docstring=True \
    -D napoleon_numpy_docstring=True \
    -D autodoc_docstring_signature=1 \
    -D autodoc_preserve_defaults=1 \
    -D autodoc_inherit_docstrings=1 \
    . _build/html

if [ $? -eq 0 ]; then
    echo ""
    echo "[serve_docs.sh] Step 3: HTML documentation built successfully!"
    echo "[serve_docs.sh] Step 4: Starting HTTP server on port 8080..."
    echo "[serve_docs.sh] Server will be available at: http://localhost:8080"
    echo "[serve_docs.sh] Press Ctrl+C to stop the server gracefully."
    echo ""

    # Start the HTTP server
    cd /app/docs/_build/html
    exec /home/appuser/.nypai-chatbot/venv-docs/bin/python -m http.server 8080
else
    echo ""
    echo "[serve_docs.sh] ❌ HTML documentation build failed!"
    echo "[serve_docs.sh] Check the error messages above."
    exit 1
fi
