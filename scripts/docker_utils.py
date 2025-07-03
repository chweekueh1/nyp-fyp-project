import os
import sys
import subprocess
import shutil
import time
from infra_utils import setup_logging
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
DOCKER_VENV_PATH = "/home/appuser/.nypai-chatbot/venv"
DOCKER_VENV_PYTHON = os.path.join(DOCKER_VENV_PATH, "bin", "python")


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
    print(
        "🐳 [DEBUG] Dockerfile will install venv at: /home/appuser/.nypai-chatbot/venv"
    )
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
    print(
        "🐳 [DEBUG] Dockerfile will install venv at: /home/appuser/.nypai-chatbot/venv"
    )
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
    print(
        "🐳 [DEBUG] Dockerfile will install venv at: /home/appuser/.nypai-chatbot/venv"
    )
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


def get_docker_volume_path(local_path: str) -> str:
    if sys.platform == "win32":
        return local_path.replace("\\", "/")
    return local_path


def docker_run():
    check_env_file(ENV_FILE_PATH)
    ensure_docker_image()
    print("🐳 Running the development Docker container...")
    logger.info("Running the development Docker container.")
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
        "-p",
        "7860:7860",
        "nyp-fyp-chatbot-dev",
    ]
    try:
        subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)
        logger.info("Development Docker container exited.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Development Docker container exited with an error: {e}")
        logger.error(
            f"Development Docker container exited with an error: {e}", exc_info=True
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during Docker run: {e}")
        logger.error(f"Unexpected error during Docker run: {e}", exc_info=True)
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
