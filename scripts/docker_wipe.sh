#!/bin/bash
# Docker Wipe Script - Complete Docker cleanup for NYP FYP Chatbot

set -e

echo "🚀 Docker Wipe Script for NYP FYP Chatbot"
echo "=========================================="
echo ""

# Function to run command with error handling
run_cmd() {
    local cmd="$1"
    local desc="$2"
    echo "🔧 $desc..."
    if eval "$cmd" 2>/dev/null; then
        echo "✅ $desc completed"
    else
        echo "ℹ️ $desc - nothing to clean or already clean"
    fi
}

# Show initial Docker info
echo "📊 BEFORE CLEANUP:"
echo "Containers: $(docker ps -aq | wc -l)"
echo "Images: $(docker images -aq | wc -l)"
echo ""

# Stop all containers
run_cmd "docker stop \$(docker ps -q)" "Stopping all running containers"

# Remove all containers
run_cmd "docker rm -f \$(docker ps -aq)" "Removing all containers"

# Remove all images
run_cmd "docker rmi -f \$(docker images -aq)" "Removing all images"

# Prune build cache
run_cmd "docker builder prune -af" "Pruning build cache"

# Prune volumes
run_cmd "docker volume prune -f" "Pruning unused volumes"

# Prune networks
run_cmd "docker network prune -f" "Pruning unused networks"

# System prune (final cleanup)
run_cmd "docker system prune -af --volumes" "Running system prune"

echo ""
echo "📊 AFTER CLEANUP:"
echo "Containers: $(docker ps -aq | wc -l)"
echo "Images: $(docker images -aq | wc -l)"
echo ""
echo "🎉 Docker wipe completed successfully!"
echo "=========================================="
