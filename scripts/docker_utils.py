"""
Docker Utilities for NYP FYP Chatbot

This script provides functions for building, running, and managing Docker containers and images for development, testing, and documentation environments. It includes helpers for environment checks, venv management, and Docker daemon control.
"""

import os
import sys
import subprocess
import shutil
import time
from infra_utils import setup_logging, get_docker_venv_path
from env_utils import check_env_file

logger = setup_logging()

ENV_FILE_PATH = os.environ.get("DOCKER_ENV_FILE", ".env")

if os.name == "nt":
    LOCAL_VENV_PATH = os.path.expanduser(r"~/.nypai-chatbot/venv")
    LOCAL_VENV_PATH = os.path.expanduser(os.path.join("~", ".nypai-chatbot", "venv"))
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "Scripts", "python.exe")
else:
    LOCAL_VENV_PATH = os.path.expanduser("~/.nypai-chatbot/venv")
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "bin", "python")


def running_in_docker() -> bool:
    return os.path.exists("/.dockerenv") or os.environ.get("IN_DOCKER") == "1"


def ensure_docker_running() -> None:
    if shutil.which("docker") is None:
        print("❌ Docker is not installed or not in PATH. Please install Docker first.")
        logger.error("Docker executable not found in PATH.")
        sys.exit(1)
    try:
        logger.info("Checking if Docker daemon is running with 'docker info'.")
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✅ Docker daemon is already running.")
        logger.info("Docker daemon is already running.")
        return
    except subprocess.CalledProcessError:
        print("⚠️  Docker daemon is not running. Attempting to start it...")
        logger.warning("Docker daemon is not running. Attempting to start.")
        if sys.platform == "linux":
            print(
                "Attempting to start Docker daemon with 'sudo systemctl start docker'..."
            )
            logger.info("Attempting to start Docker daemon via systemctl (Linux).")
            try:
                subprocess.run(
                    ["sudo", "systemctl", "start", "docker"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                for i in range(1, 11):
                    try:
                        subprocess.run(
                            ["docker", "info"],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        print("✅ Docker daemon started successfully.")
                        logger.info("Docker daemon started successfully.")
                        return
                    except subprocess.CalledProcessError:
                        print(f"Waiting for Docker to start... ({i}/10)")
                        time.sleep(2)
                print(
                    "❌ Docker daemon could not be started automatically after multiple retries."
                )
                print("Please start it manually with: 'sudo systemctl start docker'")
                logger.error(
                    "Failed to start Docker daemon automatically after retries."
                )
                sys.exit(1)
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to execute 'sudo systemctl start docker': {e}")
                print(
                    "Please ensure you have sudo privileges and Docker is correctly configured."
                )
                logger.error(f"Failed to execute systemctl command: {e}", exc_info=True)
                sys.exit(1)
            except Exception as e:
                print(
                    f"❌ An unexpected error occurred while trying to start Docker: {e}"
                )
                print("Please start Docker manually.")
                logger.error(
                    f"Unexpected error when starting Docker: {e}", exc_info=True
                )
                sys.exit(1)
        elif sys.platform == "darwin":
            print(
                "❌ Docker daemon is not running. Please start Docker Desktop from your Applications folder."
            )
            logger.error(
                "Docker not running on macOS. User advised to start Docker Desktop."
            )
            sys.exit(1)
        elif sys.platform == "win32":
            print(
                "❌ Docker daemon is not running. Please start Docker Desktop from your Start menu."
            )
            logger.error(
                "Docker not running on Windows. User advised to start Docker Desktop."
            )
            sys.exit(1)
        else:
            print(
                "❌ Docker daemon is not running. Please consult your OS documentation to start Docker."
            )
            logger.error(
                "Docker not running on unsupported OS. User advised to start manually."
            )
            sys.exit(1)
    except FileNotFoundError:
        print(
            "❌ 'docker' command not found. Please ensure Docker is installed and in your PATH."
        )
        logger.error(
            "'docker' command not found. Docker might not be installed correctly."
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred while checking Docker status: {e}")
        logger.error(
            f"Unexpected error while checking Docker status: {e}", exc_info=True
        )
        sys.exit(1)


def docker_build():
    ensure_docker_running()
    print(f"🐳 [DEBUG] Dockerfile will install venv at: {get_docker_venv_path('dev')}")
    print(
        "🐳 [DEBUG] Docker containers will load environment variables from .env via --env-file"
    )
    print("🧹 Removing old Docker image 'nyp-fyp-chatbot-dev' (if exists)...")
    try:
        subprocess.run(
            ["docker", "rmi", "-f", "nyp-fyp-chatbot-dev"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    print("🔨 Building Docker image 'nyp-fyp-chatbot-dev' with CPU optimizations...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-dev' with optimizations.")
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    env["COMPOSE_DOCKER_CLI_BUILD"] = "1"
    cpu_count = os.cpu_count() or 1
    build_args = [
        "docker",
        "build",
        "--progress=plain",
        "-f",
        "Dockerfile.dev",
        "-t",
        "nyp-fyp-chatbot-dev",
        "--build-arg",
        f"CPU_COUNT={cpu_count}",
        ".",
    ]
    start_time = time.time()
    try:
        subprocess.run(build_args, check=True, env=env)
        build_duration = int(time.time() - start_time)
        print(
            f"✅ Docker image 'nyp-fyp-chatbot-dev' built successfully in {build_duration} seconds."
        )
        logger.info(
            f"Docker image 'nyp-fyp-chatbot-dev' built successfully in {build_duration} seconds."
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        logger.error(f"Failed to build Docker image: {e}", exc_info=True)
        sys.exit(1)


def docker_build_test():
    ensure_docker_running()
    print(f"🐳 [DEBUG] Dockerfile will install venv at: {get_docker_venv_path('test')}")
    print(
        "🐳 [DEBUG] Docker containers will load environment variables from .env via --env-file"
    )
    print("🧹 Removing old Docker image 'nyp-fyp-chatbot-test' (if exists)...")
    try:
        subprocess.run(
            ["docker", "rmi", "-f", "nyp-fyp-chatbot-test"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    print("🔨 Building Docker image 'nyp-fyp-chatbot-test' with CPU optimizations...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-test' with optimizations.")
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    env["COMPOSE_DOCKER_CLI_BUILD"] = "1"
    cpu_count = os.cpu_count() or 1
    build_args = [
        "docker",
        "build",
        "--progress=plain",
        "-f",
        "Dockerfile.test",
        "-t",
        "nyp-fyp-chatbot-test",
        "--build-arg",
        f"CPU_COUNT={cpu_count}",
        ".",
    ]
    start_time = time.time()
    try:
        subprocess.run(build_args, check=True, env=env)
        build_duration = int(time.time() - start_time)
        print(
            f"✅ Docker image 'nyp-fyp-chatbot-test' built successfully in {build_duration} seconds."
        )
        logger.info(
            f"Docker image 'nyp-fyp-chatbot-test' built successfully in {build_duration} seconds."
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        logger.error(f"Failed to build Docker image: {e}", exc_info=True)
        sys.exit(1)


def docker_build_prod():
    ensure_docker_running()
    print(f"🐳 [DEBUG] Dockerfile will install venv at: {get_docker_venv_path('prod')}")
    print(
        "🐳 [DEBUG] Docker containers will load environment variables from .env via --env-file"
    )
    print("🧹 Removing old Docker image 'nyp-fyp-chatbot-prod' (if exists)...")
    try:
        subprocess.run(
            ["docker", "rmi", "-f", "nyp-fyp-chatbot-prod"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass
    print("🔨 Building Docker image 'nyp-fyp-chatbot-prod' with CPU optimizations...")
    logger.info("Building Docker image 'nyp-fyp-chatbot-prod' with optimizations.")
    env = os.environ.copy()
    env["DOCKER_BUILDKIT"] = "1"
    env["COMPOSE_DOCKER_CLI_BUILD"] = "1"
    cpu_count = os.cpu_count() or 1
    build_args = [
        "docker",
        "build",
        "--progress=plain",
        "-f",
        "Dockerfile",
        "-t",
        "nyp-fyp-chatbot-prod",
        "--build-arg",
        f"CPU_COUNT={cpu_count}",
        ".",
    ]
    start_time = time.time()
    try:
        subprocess.run(build_args, check=True, env=env)
        build_duration = int(time.time() - start_time)
        print(
            f"✅ Docker image 'nyp-fyp-chatbot-prod' built successfully in {build_duration} seconds."
        )
        logger.info(
            f"Docker image 'nyp-fyp-chatbot-prod' built successfully in {build_duration} seconds."
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to build Docker image: {e}")
        logger.error(f"Failed to build Docker image: {e}", exc_info=True)
        sys.exit(1)


def docker_build_all():
    print("\n🔨 Building test image...")
    docker_build_test()
    print("\n🔨 Building dev image...")
    docker_build()
    print("\n🔨 Building prod image...")
    docker_build_prod()
    print("\n✅ All Docker images built successfully.")


def ensure_docker_image():
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot-dev"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            print("✅ Docker image 'nyp-fyp-chatbot-dev' exists.")
            logger.info("Docker image 'nyp-fyp-chatbot-dev' exists.")
            return
        else:
            print("🔨 Docker image 'nyp-fyp-chatbot-dev' not found. Building...")
            logger.info("Docker image 'nyp-fyp-chatbot-dev' not found. Building.")
            docker_build()
    except Exception as e:
        print(f"❌ Error checking/building Docker image: {e}")
        logger.error(f"Error checking/building Docker image: {e}", exc_info=True)
        sys.exit(1)


def ensure_test_docker_image():
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot-test"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            print("✅ Docker image 'nyp-fyp-chatbot-test' exists.")
            logger.info("Docker image 'nyp-fyp-chatbot-test' exists.")
            return
        else:
            print("🔨 Docker image 'nyp-fyp-chatbot-test' not found. Building...")
            logger.info("Docker image 'nyp-fyp-chatbot-test' not found. Building.")
            docker_build_test()
    except Exception as e:
        print(f"❌ Error checking/building Docker test image: {e}")
        logger.error(f"Error checking/building Docker test image: {e}", exc_info=True)
        sys.exit(1)


def ensure_prod_docker_image():
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "nyp-fyp-chatbot-prod"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            print("✅ Docker image 'nyp-fyp-chatbot-prod' exists.")
            logger.info("Docker image 'nyp-fyp-chatbot-prod' exists.")
            return
        else:
            print("🔨 Docker image 'nyp-fyp-chatbot-prod' not found. Building...")
            logger.info("Docker image 'nyp-fyp-chatbot-prod' not found. Building.")
            docker_build_prod()
    except Exception as e:
        print(f"❌ Error checking/building Docker prod image: {e}")
        logger.error(f"Error checking/building Docker prod image: {e}", exc_info=True)
        sys.exit(1)


def get_docker_volume_path(local_path: str) -> str:
    if sys.platform == "win32":
        return local_path.replace("\\", "/")
    return local_path


def docker_run(mode="dev", prompt_for_mode=False, plaintext=False):
    check_env_file(ENV_FILE_PATH)

    # If prompt_for_mode is True, ask user to choose container type
    if prompt_for_mode:
        print("🐳 Which Docker container would you like to run?")
        print("1. Development (dev) - Port 7680")
        print("2. Production (prod) - Port 7860")
        print("3. Test (test) - Port 7861")
        print()

        while True:
            try:
                choice = input("Enter your choice (1-3) [default: 1]: ").strip()
                if choice == "" or choice == "1":
                    mode = "dev"
                    break
                elif choice == "2":
                    mode = "prod"
                    break
                elif choice == "3":
                    mode = "test"
                    break
                else:
                    print("❌ Invalid choice. Please enter 1, 2, or 3.")
            except (KeyboardInterrupt, EOFError):
                print("\n❌ Operation cancelled by user.")
                sys.exit(1)

    # Map mode to Docker image
    image_map = {
        "test": "nyp-fyp-chatbot-test",
        "prod": "nyp-fyp-chatbot-prod",
        "dev": "nyp-fyp-chatbot-dev",
    }
    image = image_map.get(mode, "nyp-fyp-chatbot-dev")

    # Ensure the appropriate image exists
    if mode == "test":
        ensure_test_docker_image()
    elif mode == "prod":
        ensure_prod_docker_image()
    else:
        ensure_docker_image()

    # Import here to avoid circular imports
    from infra_utils import get_docker_venv_path

    venv_path = get_docker_venv_path(mode)
    print(f"🐳 [DEBUG] Dockerfile installs venv at: {venv_path}")
    print(
        f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
    )
    print(f"🐳 Starting {mode} Docker container...")
    logger.info(f"Starting {mode} Docker container.")

    # Configure port mapping based on Docker mode
    if mode == "dev":
        # Dev mode: map host 7680 to container 7680
        port_mapping = "7680:7680"
    elif mode == "test":
        # Test mode: map host 7861 to container 7861
        port_mapping = "7861:7861"
    else:  # prod mode
        # Prod mode: map host 7860 to container 7860
        port_mapping = "7860:7860"

    # For dev/test modes, we don't mount the volume to avoid overriding the venv
    # Only mount specific directories that need persistence
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--env-file",
        ENV_FILE_PATH,
        "-p",
        port_mapping,
        image,
    ]
    if plaintext:
        cmd.append("--plaintext")

    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        logger.info(f"{mode.capitalize()} Docker container exited.")
    except subprocess.CalledProcessError as e:
        print(f"❌ {mode.capitalize()} Docker container exited with an error: {e}")
        logger.error(
            f"{mode.capitalize()} Docker container exited with an error: {e}",
            exc_info=True,
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during {mode} Docker run: {e}")
        logger.error(f"Unexpected error during {mode} Docker run: {e}", exc_info=True)
        sys.exit(1)


def docker_shell():
    check_env_file(ENV_FILE_PATH)
    ensure_docker_image()
    print("🐳 Opening a shell in the development Docker container...")
    logger.info("Opening a shell in development Docker container.")
    chatbot_dir = os.path.expanduser("~/.nypai-chatbot")
    docker_volume_path = get_docker_volume_path(chatbot_dir)
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--env-file",
        ENV_FILE_PATH,
        "-v",
        f"{docker_volume_path}:/home/appuser/.nypai-chatbot",
        "nyp-fyp-chatbot-dev",
        "/bin/bash",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        logger.info("Development Docker shell session exited.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Development Docker shell session exited with an error: {e}")
        logger.error(
            f"Development Docker shell session exited with an error: {e}", exc_info=True
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during development Docker shell: {e}")
        logger.error(
            f"Unexpected error during development Docker shell: {e}", exc_info=True
        )
        sys.exit(1)


def docker_export():
    ensure_docker_image()
    output_file = "nyp-fyp-chatbot.tar"
    print(f"📦 Exporting Docker image 'nyp-fyp-chatbot' to {output_file} ...")
    logger.info(f"Exporting Docker image to {output_file}.")
    try:
        subprocess.run(
            ["docker", "save", "-o", output_file, "nyp-fyp-chatbot"],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        print(f"✅ Docker image exported successfully to {output_file}")
        logger.info("Docker image exported successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to export Docker image: {e}")
        logger.error(f"Failed to export Docker image: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker export: {e}")
        logger.error(f"Unexpected error during Docker export: {e}", exc_info=True)
        sys.exit(1)


def docker_cleanup(options=None):
    """Clean up Docker resources with various options."""
    if options is None:
        options = ["all"]

    print("🧹 Docker Cleanup Starting...")
    logger.info("Starting Docker cleanup operation")

    # Show current Docker status
    try:
        containers = subprocess.run(
            [
                "docker",
                "ps",
                "-a",
                "--format",
                "table {{.Names}}\t{{.Status}}\t{{.Size}}",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        images = subprocess.run(
            [
                "docker",
                "images",
                "--format",
                "table {{.Repository}}\t{{.Tag}}\t{{.Size}}",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

        print("\n📊 Current Docker Status:")
        print("Containers:")
        print(containers if containers else "No containers found")
        print("\nImages:")
        print(images if images else "No images found")

        # Get system info
        system_df = subprocess.run(
            ["docker", "system", "df"], capture_output=True, text=True, check=True
        ).stdout.strip()
        print(f"\nSystem Usage:\n{system_df}")

    except subprocess.CalledProcessError:
        print("⚠️  Could not get Docker status (Docker may not be running)")
        logger.warning("Could not get Docker status - Docker may not be running")

    if "all" in options or "containers" in options:
        print("\n🗑️  Removing all containers...")
        logger.info("Removing all Docker containers")
        try:
            subprocess.run(["docker", "container", "prune", "-f"], check=False)
            subprocess.run(
                "docker rm -f $(docker ps -aq) 2>/dev/null || true",
                shell=True,
                check=False,
            )
        except Exception as e:
            logger.warning(f"Error removing containers: {e}")

    if "all" in options or "images" in options:
        print("🗑️  Removing all images...")
        logger.info("Removing all Docker images")
        try:
            subprocess.run(["docker", "image", "prune", "-af"], check=False)
            subprocess.run(
                "docker rmi -f $(docker images -aq) 2>/dev/null || true",
                shell=True,
                check=False,
            )
        except Exception as e:
            logger.warning(f"Error removing images: {e}")

    if "all" in options or "cache" in options:
        print("🗑️  Clearing build cache...")
        logger.info("Clearing Docker build cache")
        try:
            subprocess.run(["docker", "builder", "prune", "-af"], check=False)
        except Exception as e:
            logger.warning(f"Error clearing build cache: {e}")

    if "all" in options or "volumes" in options:
        print("🗑️  Removing volumes...")
        logger.info("Removing Docker volumes")
        try:
            subprocess.run(["docker", "volume", "prune", "-f"], check=False)
        except Exception as e:
            logger.warning(f"Error removing volumes: {e}")

    if "all" in options or "networks" in options:
        print("🗑️  Removing networks...")
        logger.info("Removing Docker networks")
        try:
            subprocess.run(["docker", "network", "prune", "-f"], check=False)
        except Exception as e:
            logger.warning(f"Error removing networks: {e}")

    if "all" in options:
        print("🗑️  Complete system cleanup...")
        logger.info("Performing complete Docker system cleanup")
        try:
            subprocess.run(
                ["docker", "system", "prune", "-af", "--volumes"], check=False
            )
        except Exception as e:
            logger.warning(f"Error in system cleanup: {e}")

    print("\n✅ Docker cleanup completed!")
    logger.info("Docker cleanup completed successfully")

    # Show final status
    try:
        final_df = subprocess.run(
            ["docker", "system", "df"], capture_output=True, text=True, check=True
        ).stdout.strip()
        print(f"\nFinal System Usage:\n{final_df}")
    except Exception as e:
        logger.warning(f"Could not get final Docker status: {e}")


def docker_wipe():
    """Complete Docker wipe - removes everything."""
    print(
        "🚨 WARNING: This will remove ALL Docker containers, images, volumes, networks, and cache!"
    )
    print("This action cannot be undone.")

    # In non-interactive mode or if explicitly confirmed, proceed
    if "--force" in sys.argv or "--docker-wipe" in sys.argv:
        print("🧹 Proceeding with complete Docker wipe...")
        logger.info("Starting complete Docker wipe operation")
        docker_cleanup(["all"])
    else:
        try:
            response = (
                input("Are you sure you want to continue? (yes/no): ").lower().strip()
            )
            if response in ["yes", "y"]:
                print("🧹 Proceeding with complete Docker wipe...")
                logger.info("User confirmed complete Docker wipe operation")
                docker_cleanup(["all"])
            else:
                print("❌ Docker wipe cancelled.")
                logger.info("Docker wipe cancelled by user")
                return
        except KeyboardInterrupt:
            print("\n❌ Docker wipe cancelled.")
            logger.info("Docker wipe cancelled by user (KeyboardInterrupt)")
            return
