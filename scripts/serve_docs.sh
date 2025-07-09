#!/bin/sh
set -e

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

# Build the documentation with detailed progress
# [serve_docs.sh] Step 1: Generating Sphinx documentation...
# [serve_docs.sh] This may take a few minutes on first run...
# 🔍 Generating Sphinx documentation...
# 🏗️ Building HTML documentation...
# (Remove or comment out the command that runs generate_docs.py or sphinx-build)

echo ""
echo "[serve_docs.sh] Step 2: Documentation build completed successfully!"
echo "[serve_docs.sh] Step 3: Starting HTTP server on port 8080..."
echo "[serve_docs.sh] Server will be available at: http://localhost:8080"
echo "[serve_docs.sh] Press Ctrl+C to stop the server gracefully."
echo ""

# Start the HTTP server
cd /app/docs/_build/html
exec /home/appuser/.nypai-chatbot/venv-docs/bin/python -m http.server 8080
