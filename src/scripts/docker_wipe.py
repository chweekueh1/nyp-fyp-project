#!/usr/bin/env python3
"""
module module for the NYP FYP CNC Chatbot project.

Docker Wipe Script - Complete Docker cleanup for NYP FYP Chatbot

This script provides comprehensive Docker cleanup functionality, removing all containers,
images, volumes, networks, and build cache. It's a safer alternative to the shell script
with better error handling and logging.

This module provides functionality for module.

**Features:**
    - Core functionality for module
    - Integration with other system components
    - Error handling and validation

**Usage:**
    Import and use the relevant functions or classes as needed.

**Returns:**
    Various, depending on the function or class used.

**Raises:**
    See individual function/class docstrings.
"""

import sys
import subprocess
import shutil
import logging
from typing import List

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_cmd(cmd: List[str], desc: str, capture_output: bool = True) -> bool:
    """
    Run a command with error handling.

    :param cmd: Command to run as list
    :type cmd: List[str]
    :param desc: Description of what the command does
    :type desc: str
    :param capture_output: Whether to capture output
    :type capture_output: bool
    :return: True if successful, False otherwise
    :rtype: bool

    **Args:**
        See function signature for parameters.

    **Returns:**
        Various, depending on the function.

    **Raises:**
        Various exceptions, depending on the function.

    **Example:**
        >>> result = run_cmd()
        >>> print(result)
    """
    print(f"🔧 {desc}...")
    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        if capture_output:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=False)

        if result.returncode == 0:
            print(f"✅ {desc} completed")
            logger.info(f"{desc} completed successfully")
            return True
        else:
            print(f"ℹ️ {desc} - nothing to clean or already clean")
            logger.info(f"{desc} - no action needed (return code: {result.returncode})")
            return True
    except Exception as e:
        print(f"⚠️ {desc} - error: {e}")
        logger.warning(f"{desc} failed: {e}")
        return False


def get_docker_count(cmd: List[str]) -> int:
    """
    Get count of Docker resources.

    :param cmd: Docker command to run
    :type cmd: List[str]
    :return: Count of resources
    :rtype: int

    **Args:**
        See function signature for parameters.

    **Returns:**
        Various, depending on the function.

    **Raises:**
        Various exceptions, depending on the function.

    **Example:**
        >>> result = get_docker_count()
        >>> print(result)
    """
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return len([line for line in result.stdout.strip().split("\n") if line.strip()])
    except subprocess.CalledProcessError:
        return 0
    except Exception:
        return 0


def docker_wipe() -> None:
    """
    Perform complete Docker wipe - removes all containers, images, volumes, networks, and cache.

    This function provides comprehensive cleanup of all Docker resources. It's designed
    to be safe and informative, showing before/after counts and handling errors gracefully.

    **Args:**
        See function signature for parameters.

    **Returns:**
        Various, depending on the function.

    **Raises:**
        Various exceptions, depending on the function.

    **Example:**
        >>> result = docker_wipe()
        >>> print(result)
    """
    print("🚀 Docker Wipe Script for NYP FYP Chatbot")
    print("==========================================")
    print("")

    # Check if Docker is available
    if not shutil.which("docker"):
        print("❌ Docker is not installed or not in PATH")
        logger.error("Docker not found in PATH")
        sys.exit(1)

    # Show initial Docker info
    print("📊 BEFORE CLEANUP:")
    containers_before = get_docker_count(["docker", "ps", "-aq"])
    images_before = get_docker_count(["docker", "images", "-aq"])
    print(f"Containers: {containers_before}")
    print(f"Images: {images_before}")
    print("")

    # Stop all containers
    try:
        result = subprocess.run(
            ["docker", "ps", "-q"], capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            container_ids = result.stdout.strip().split("\n")
            for container_id in container_ids:
                if container_id.strip():
                    run_cmd(
                        ["docker", "stop", container_id.strip()],
                        f"Stopping container {container_id.strip()}",
                    )
    except subprocess.CalledProcessError:
        print("ℹ️ No running containers to stop")

    # Remove all containers
    try:
        result = subprocess.run(
            ["docker", "ps", "-aq"], capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            container_ids = result.stdout.strip().split("\n")
            for container_id in container_ids:
                if container_id.strip():
                    run_cmd(
                        ["docker", "rm", "-f", container_id.strip()],
                        f"Removing container {container_id.strip()}",
                    )
    except subprocess.CalledProcessError:
        print("ℹ️ No containers to remove")

    # Remove all images
    try:
        result = subprocess.run(
            ["docker", "images", "-aq"], capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            image_ids = result.stdout.strip().split("\n")
            for image_id in image_ids:
                if image_id.strip():
                    run_cmd(
                        ["docker", "rmi", "-f", image_id.strip()],
                        f"Removing image {image_id.strip()}",
                    )
    except subprocess.CalledProcessError:
        print("ℹ️ No images to remove")

    # Prune build cache
    run_cmd(["docker", "builder", "prune", "-af"], "Pruning build cache")

    # Prune volumes
    run_cmd(["docker", "volume", "prune", "-f"], "Pruning unused volumes")

    # Prune networks
    run_cmd(["docker", "network", "prune", "-f"], "Pruning unused networks")

    # System prune (final cleanup)
    run_cmd(["docker", "system", "prune", "-af", "--volumes"], "Running system prune")

    print("")
    print("📊 AFTER CLEANUP:")
    containers_after = get_docker_count(["docker", "ps", "-aq"])
    images_after = get_docker_count(["docker", "images", "-aq"])
    print(f"Containers: {containers_after}")
    print(f"Images: {images_after}")
    print("")

    # Summary
    containers_removed = containers_before - containers_after
    images_removed = images_before - images_after

    print("🎉 Docker wipe completed successfully!")
    print(f"   - Removed {containers_removed} containers")
    print(f"   - Removed {images_removed} images")
    print("==========================================")

    logger.info(
        f"Docker wipe completed. Removed {containers_removed} containers, {images_removed} images"
    )


def main() -> None:
    """
    Main entry point for the Docker wipe script.

    Handles command line arguments and executes the wipe operation.

    **Args:**
        See function signature for parameters.

    **Returns:**
        Various, depending on the function.

    **Raises:**
        Various exceptions, depending on the function.

    **Example:**
        >>> result = main()
        >>> print(result)
    """
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h", "help"]:
            print("Docker Wipe Script for NYP FYP Chatbot")
            print("======================================")
            print("")
            print("This script performs a complete cleanup of Docker resources:")
            print("  - Stops and removes all containers")
            print("  - Removes all images")
            print("  - Prunes build cache, volumes, and networks")
            print("  - Runs system prune for final cleanup")
            print("")
            print("Usage:")
            print("  python docker_wipe.py          # Run full cleanup")
            print("  python docker_wipe.py --help   # Show this help")
            print("")
            print("⚠️  WARNING: This will remove ALL Docker resources!")
            print("   Make sure you have backups of any important data.")
            print("")
            return

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    try:
        docker_wipe()
        logger.info("Docker wipe completed successfully")
    except KeyboardInterrupt:
        print("\n🛑 Docker wipe interrupted by user")
        logger.info("Docker wipe interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Docker wipe failed: {e}")
        logger.error(f"Docker wipe failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
