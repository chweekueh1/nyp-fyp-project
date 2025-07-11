#!/usr/bin/env python3
"""
Main script for running various NYP FYP Chatbot operations.

This script provides a command-line interface for running tests, benchmarks,
and other operations in the NYP FYP Chatbot project.
"""

import sys
import subprocess
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import argparse
from docker_utils import (
    docker_build,
    docker_build_test,
    docker_build_prod,
    docker_build_all,
    docker_run,
    ensure_test_docker_image,
    docker_shell,
    docker_export,
    docker_cleanup,
    docker_wipe,
)
from test_utils import (
    docker_test,
    docker_test_suite,
    docker_test_file,
    list_available_tests,
)
from env_utils import ENV_FILE_PATH, running_in_docker, logger
from precommit_utils import setup_pre_commit
from fix_permissions import fix_nypai_chatbot_permissions
from infra_utils import get_docker_venv_path

fix_nypai_chatbot_permissions()


def main():
    parser = argparse.ArgumentParser(
        description="NYP FYP Chatbot Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build different Docker containers with CPU optimizations
  python setup.py --docker-build          # Build development container
  python setup.py --docker-build-test     # Build test container
  python setup.py --docker-build-prod     # Build production container
  python setup.py --docker-build-all      # Build all containers

  # Run Docker container (prompts to choose dev/prod/test)
  python setup.py --docker-run

  # Run performance benchmarks
  python setup.py --run-benchmarks                                # Run comprehensive benchmarks

  # Run specific container without prompt
  python setup.py --docker-run --docker-mode dev     # Development container (port 7680)
  python setup.py --docker-run --docker-mode prod    # Production container (port 7860)
  python setup.py --docker-run --docker-mode test    # Test container (port 7861)

  # Run tests in test container
  python setup.py --docker-test                                    # Run environment verification
  python setup.py --docker-test-suite frontend                     # Run frontend test suite
  python setup.py --docker-test-suite backend                      # Run backend test suite
  python setup.py --docker-test-suite integration                  # Run integration test suite
  python setup.py --docker-test-suite performance                  # Run performance test suite
  python setup.py --docker-test-suite comprehensive                # Run comprehensive test suite
  python setup.py --docker-test-suite all                          # Run all test suites
  python setup.py --docker-test-file tests/backend/test_backend_fixes_and_rename.py
  python setup.py --list-tests                                    # List all available tests

  # Development tools
  python setup.py --docker-shell
  python setup.py --setup-pre-commit

  # Docker cleanup tools
  python setup.py --docker-cleanup                                 # Clean up all Docker resources
  python setup.py --docker-cleanup-containers                     # Clean up containers only
  python setup.py --docker-cleanup-images                         # Clean up images only
  python setup.py --docker-cleanup-cache                          # Clean up build cache only
  python setup.py --docker-cleanup-volumes                        # Clean up volumes only
  python setup.py --docker-cleanup-networks                       # Clean up networks only
  python setup.py --docker-wipe                                   # Complete Docker wipe (WARNING: destructive)
  python setup.py --docker-wipe --force                           # Force wipe without confirmation
        """,
    )

    # Docker commands
    parser.add_argument(
        "--docker-build",
        action="store_true",
        help="Build the development Docker image 'nyp-fyp-chatbot-dev' with CPU optimizations",
    )
    parser.add_argument(
        "--docker-build-test",
        action="store_true",
        help="Build the test Docker image 'nyp-fyp-chatbot-test' with CPU optimizations",
    )
    parser.add_argument(
        "--docker-build-prod",
        action="store_true",
        help="Build the production Docker image 'nyp-fyp-chatbot-prod' with CPU optimizations",
    )
    parser.add_argument(
        "--docker-build-all",
        action="store_true",
        help="Build all Docker images (dev, test, prod) with CPU optimizations",
    )

    parser.add_argument(
        "--docker-run",
        action="store_true",
        help="Run a Docker container (prompts to choose between dev, prod, or test)",
    )
    parser.add_argument(
        "--run-benchmarks",
        action="store_true",
        help="Run performance benchmarks in the dev container",
    )
    parser.add_argument(
        "--docker-test",
        action="store_true",
        help="Run all tests in test Docker container",
    )
    parser.add_argument(
        "--docker-test-suite",
        type=str,
        choices=[
            "frontend",
            "backend",
            "integration",
            "comprehensive",
            "unit",
            "performance",
            "all",
            "demo",
        ],
        help="Run a specific test suite in test Docker container",
    )
    parser.add_argument(
        "--docker-test-file",
        type=str,
        help="Run an individual test file in test Docker container",
    )
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List all available test files and suites",
    )
    parser.add_argument(
        "--docker-shell",
        action="store_true",
        help="Open a shell in the development Docker container",
    )
    parser.add_argument(
        "--docker-export",
        action="store_true",
        help="Export the Docker image to a tar file",
    )

    # Docker cleanup commands
    parser.add_argument(
        "--docker-cleanup",
        action="store_true",
        help="Clean up Docker resources (containers, images, cache, volumes, networks)",
    )
    parser.add_argument(
        "--docker-cleanup-containers",
        action="store_true",
        help="Clean up Docker containers only",
    )
    parser.add_argument(
        "--docker-cleanup-images",
        action="store_true",
        help="Clean up Docker images only",
    )
    parser.add_argument(
        "--docker-cleanup-cache",
        action="store_true",
        help="Clean up Docker build cache only",
    )
    parser.add_argument(
        "--docker-cleanup-volumes",
        action="store_true",
        help="Clean up Docker volumes only",
    )
    parser.add_argument(
        "--docker-cleanup-networks",
        action="store_true",
        help="Clean up Docker networks only",
    )
    parser.add_argument(
        "--docker-wipe",
        action="store_true",
        help="Complete Docker wipe - removes ALL Docker resources (WARNING: destructive)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force operation without confirmation prompts",
    )

    # Development tools
    parser.add_argument(
        "--setup-pre-commit",
        action="store_true",
        help="Install pre-commit hooks with ruff for code quality checks.",
    )

    # Internal Docker container arguments
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help="Run tests inside Docker container (internal use)",
    )

    parser.add_argument(
        "--docker-mode",
        type=str,
        choices=["test", "prod", "dev"],
        default="test",
        help="Select which Docker image/venv to use for test commands (default: test)",
    )

    args = parser.parse_args()

    # Handle Docker commands
    if args.docker_build:
        docker_build()
        return
    elif args.docker_build_test:
        docker_build_test()
        return
    elif args.docker_build_prod:
        docker_build_prod()
        return
    elif args.docker_build_all:
        docker_build_all()
        return
    elif args.docker_run:
        # Check if docker_mode was explicitly set by user or is using default
        # If using default "test", prompt user to choose
        prompt_for_mode = "--docker-mode" not in sys.argv
        docker_run(mode=args.docker_mode, prompt_for_mode=prompt_for_mode)
        return
    elif args.docker_test:
        ensure_test_docker_image()
        print(
            "🐳 [DEBUG] Dockerfile installs venv at: "
            + get_docker_venv_path(args.docker_mode)
        )
        print(
            f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
        )
        print("🔍 Running environment check (scripts/check_env.py) before tests...")
        docker_test(mode=args.docker_mode)
        return
    elif args.docker_test_suite:
        ensure_test_docker_image()
        print(
            "🐳 [DEBUG] Dockerfile installs venv at: "
            + get_docker_venv_path(args.docker_mode)
        )
        print(
            f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
        )
        print("🔍 Running environment check (scripts/check_env.py) before tests...")
        docker_test_suite(args.docker_test_suite, mode=args.docker_mode)
        return
    elif args.docker_test_file:
        ensure_test_docker_image()
        print(
            "🐳 [DEBUG] Dockerfile installs venv at: "
            + get_docker_venv_path(args.docker_mode)
        )
        print(
            f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
        )
        print("🔍 Running environment check (scripts/check_env.py) before tests...")
        docker_test_file(args.docker_test_file, mode=args.docker_mode)
        return
    elif args.list_tests:
        list_available_tests()
        return
    elif args.docker_shell:
        docker_shell()
        return
    elif args.docker_export:
        docker_export()
        return

    # Handle Docker cleanup commands
    elif args.docker_cleanup:
        docker_cleanup(["all"])
        return
    elif args.docker_cleanup_containers:
        docker_cleanup(["containers"])
        return
    elif args.docker_cleanup_images:
        docker_cleanup(["images"])
        return
    elif args.docker_cleanup_cache:
        docker_cleanup(["cache"])
        return
    elif args.docker_cleanup_volumes:
        docker_cleanup(["volumes"])
        return
    elif args.docker_cleanup_networks:
        docker_cleanup(["networks"])
        return
    elif args.docker_wipe:
        docker_wipe()
        return

    # Handle development tools
    elif args.setup_pre_commit:
        setup_pre_commit()
        return

    # Handle internal Docker container arguments
    elif args.run_tests:
        print("🧪 Running test suite inside the container...")
        logger.info("Running test suite inside the container (internal call).")
        try:
            subprocess.run(
                ["python", "tests/comprehensive_test_suite.py"],
                check=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            print("✅ Tests completed successfully.")
            logger.info("Tests completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Tests failed: {e}")
            logger.error(f"Tests failed: {e}", exc_info=True)
            sys.exit(1)
        except Exception as e:
            print(f"❌ An unexpected error occurred during tests: {e}")
            logger.error(f"Unexpected error during tests: {e}", exc_info=True)
            sys.exit(1)
        return

    # This block executes if no specific argparse argument matches
    elif running_in_docker():
        print("🐳 [DEBUG] Dockerfile installs venv at: " + get_docker_venv_path("dev"))
        print(
            f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
        )
        print("🐳 Running inside Docker container...")
        logger.info("Running inside Docker container.")
        print("🚀 Starting main application...")
        logger.info("Starting main application.")
        try:
            subprocess.run(
                ["python", "src/app.py"],
                check=True,
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Application failed to start: {e}")
            logger.error(f"Application failed to start: {e}", exc_info=True)
            sys.exit(1)
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            logger.error(f"Unexpected error: {e}", exc_info=True)
            sys.exit(1)
    else:
        parser.print_help()
        print(
            "\n❌ No command specified. Please use one of the available options above."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
