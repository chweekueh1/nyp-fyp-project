#!/bin/sh
# Script to conditionally copy Docker build tracking files

set -e

# Create data directory if it doesn't exist
mkdir -p /app/data

# Check if data directory exists in build context
if [ -d ./data ]; then
    echo "Data directory found, copying build tracking files"
    cp -r ./data/* /app/data/ 2>/dev/null || echo "No files to copy"
else
    echo "No data directory found, skipping build tracking files"
fi

echo "Build data copy completed"
