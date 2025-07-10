#!/usr/bin/env python3
"""
Docker Cleanup Script for NYP FYP Chatbot

This script provides comprehensive Docker cleanup functionality including:
- Stopping and removing all containers
- Removing all images
- Clearing build cache
- Pruning volumes and networks
"""

import subprocess
import argparse
import logging
from typing import List

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def run_command(
    command: List[str], description: str, ignore_errors: bool = True
) -> bool:
    """
    Run a shell command and handle errors.

    :param command: Command to run as list of strings
    :type command: List[str]
    :param description: Description of what the command does
    :type description: str
    :param ignore_errors: Whether to ignore errors and continue
    :type ignore_errors: bool
    :return: True if successful, False otherwise
    :rtype: bool
    """
    try:
        logger.info(f"🔧 {description}...")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        if result.stdout.strip():
            logger.info(f"✅ {description} completed")
            if result.stdout.strip():
                logger.debug(f"Output: {result.stdout.strip()}")
        else:
            logger.info(f"ℹ️ {description} - nothing to clean")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            logger.warning(
                f"⚠️ {description} failed (ignored): {e.stderr.strip() if e.stderr else str(e)}"
            )
            return False
        else:
            logger.error(
                f"❌ {description} failed: {e.stderr.strip() if e.stderr else str(e)}"
            )
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during {description}: {str(e)}")
        return False


def stop_all_containers() -> bool:
    """Stop all running Docker containers."""
    return run_command(
        ["docker", "stop", "$(docker ps -q)"],
        "Stopping all running containers",
        ignore_errors=True,
    )


def remove_all_containers() -> bool:
    """Remove all Docker containers."""
    return run_command(
        ["docker", "rm", "-f", "$(docker ps -aq)"],
        "Removing all containers",
        ignore_errors=True,
    )


def remove_all_images() -> bool:
    """Remove all Docker images."""
    return run_command(
        ["docker", "rmi", "-f", "$(docker images -aq)"],
        "Removing all images",
        ignore_errors=True,
    )


def prune_build_cache() -> bool:
    """Prune Docker build cache."""
    return run_command(
        ["docker", "builder", "prune", "-af"], "Pruning build cache", ignore_errors=True
    )


def prune_volumes() -> bool:
    """Prune unused Docker volumes."""
    return run_command(
        ["docker", "volume", "prune", "-f"],
        "Pruning unused volumes",
        ignore_errors=True,
    )


def prune_networks() -> bool:
    """Prune unused Docker networks."""
    return run_command(
        ["docker", "network", "prune", "-f"],
        "Pruning unused networks",
        ignore_errors=True,
    )


def system_prune() -> bool:
    """Run Docker system prune to clean up everything."""
    return run_command(
        ["docker", "system", "prune", "-af", "--volumes"],
        "Running system prune",
        ignore_errors=True,
    )


def get_docker_info() -> None:
    """Display Docker system information before and after cleanup."""
    logger.info("📊 Docker System Information:")

    # Get container count
    try:
        result = subprocess.run(["docker", "ps", "-aq"], capture_output=True, text=True)
        container_count = len(
            [line for line in result.stdout.strip().split("\n") if line]
        )
        logger.info(f"   Containers: {container_count}")
    except Exception:
        logger.info("   Containers: Unable to count")

    # Get image count
    try:
        result = subprocess.run(
            ["docker", "images", "-aq"], capture_output=True, text=True
        )
        image_count = len([line for line in result.stdout.strip().split("\n") if line])
        logger.info(f"   Images: {image_count}")
    except Exception:
        logger.info("   Images: Unable to count")

    # Get system disk usage
    try:
        result = subprocess.run(
            ["docker", "system", "df"], capture_output=True, text=True
        )
        if result.returncode == 0:
            logger.info("   Disk Usage:")
            for line in result.stdout.strip().split("\n")[1:]:  # Skip header
                logger.info(f"     {line}")
    except Exception:
        logger.info("   Disk Usage: Unable to retrieve")


def main():
    """Main function to handle command line arguments and execute cleanup."""
    parser = argparse.ArgumentParser(
        description="Docker cleanup script for NYP FYP Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/docker_cleanup.py --all          # Complete cleanup
  python scripts/docker_cleanup.py --containers   # Remove containers only
  python scripts/docker_cleanup.py --images       # Remove images only
  python scripts/docker_cleanup.py --cache        # Clear build cache only
        """,
    )

    parser.add_argument(
        "--all", action="store_true", help="Perform complete Docker cleanup"
    )
    parser.add_argument(
        "--containers", action="store_true", help="Stop and remove all containers"
    )
    parser.add_argument("--images", action="store_true", help="Remove all images")
    parser.add_argument("--cache", action="store_true", help="Clear build cache")
    parser.add_argument("--volumes", action="store_true", help="Prune unused volumes")
    parser.add_argument("--networks", action="store_true", help="Prune unused networks")
    parser.add_argument(
        "--info", action="store_true", help="Show Docker system information"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # If no specific options, show help
    if not any(
        [
            args.all,
            args.containers,
            args.images,
            args.cache,
            args.volumes,
            args.networks,
            args.info,
        ]
    ):
        parser.print_help()
        return

    logger.info("🚀 Docker Cleanup Script for NYP FYP Chatbot")
    logger.info("=" * 60)

    # Show initial system info
    if args.info or args.all:
        logger.info("📊 BEFORE CLEANUP:")
        get_docker_info()
        logger.info("")

    success_count = 0
    total_operations = 0

    # Perform cleanup operations
    if args.all or args.containers:
        total_operations += 2
        if stop_all_containers():
            success_count += 1
        if remove_all_containers():
            success_count += 1

    if args.all or args.images:
        total_operations += 1
        if remove_all_images():
            success_count += 1

    if args.all or args.cache:
        total_operations += 1
        if prune_build_cache():
            success_count += 1

    if args.all or args.volumes:
        total_operations += 1
        if prune_volumes():
            success_count += 1

    if args.all or args.networks:
        total_operations += 1
        if prune_networks():
            success_count += 1

    if args.all:
        total_operations += 1
        if system_prune():
            success_count += 1

    # Show final system info
    if args.info or args.all:
        logger.info("")
        logger.info("📊 AFTER CLEANUP:")
        get_docker_info()

    # Summary
    logger.info("")
    logger.info("📋 Cleanup Summary:")
    logger.info(f"   Successful operations: {success_count}/{total_operations}")

    if success_count == total_operations:
        logger.info("🎉 Docker cleanup completed successfully!")
    else:
        logger.warning(
            f"⚠️ Some operations failed ({total_operations - success_count} failures)"
        )

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
