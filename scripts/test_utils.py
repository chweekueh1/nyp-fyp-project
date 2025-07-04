import os
import sys
import subprocess
from typing import Optional
from infra_utils import setup_logging

logger = setup_logging()

if os.name == "nt":
    LOCAL_VENV_PATH = os.path.expanduser(r"~/.nypai-chatbot/venv")
    LOCAL_VENV_PATH = os.path.expanduser(os.path.join("~", ".nypai-chatbot", "venv"))
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "Scripts", "python.exe")
else:
    LOCAL_VENV_PATH = os.path.expanduser("~/.nypai-chatbot/venv")
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "bin", "python")

ENV_FILE_PATH = os.environ.get("DOCKER_ENV_FILE", ".env")


def docker_test(test_target: Optional[str] = None, mode: str = "test") -> None:
    image_map = {
        "test": "nyp-fyp-chatbot-test",
        "prod": "nyp-fyp-chatbot-prod",
        "dev": "nyp-fyp-chatbot-dev",
    }
    image = image_map.get(mode, "nyp-fyp-chatbot-test")
    print(f"🐳 [DEBUG] Using Docker image: {image}")
    print(
        f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
    )

    if test_target:
        print(f"🧪 Running {test_target} in Docker container...")
        logger.info(f"Running {test_target} inside Docker container.")
        if test_target == "all":
            print("🚀 Running all tests using comprehensive test suite...")
            cmd = [
                "docker",
                "run",
                "--rm",
                "-it",
                "--env-file",
                ENV_FILE_PATH,
                image,
                "python",
                "tests/comprehensive_test_suite.py",
                "--suite",
                "all",
            ]
        elif test_target.startswith("tests/") and test_target.endswith(".py"):
            cmd = [
                "docker",
                "run",
                "--rm",
                "-it",
                "--env-file",
                ENV_FILE_PATH,
                image,
                "python",
                test_target,
            ]
        else:
            cmd = [
                "docker",
                "run",
                "--rm",
                "-it",
                "--env-file",
                ENV_FILE_PATH,
                image,
                "python",
                "tests/comprehensive_test_suite.py",
                "--suite",
                test_target,
            ]
        try:
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"❌ Failed to run {test_target} in Docker: {e}")
            logger.error(f"Failed to run {test_target} in Docker: {e}", exc_info=True)
            sys.exit(1)
    else:
        print("🧪 Running Docker environment verification...")
        logger.info("Running Docker environment verification.")
        cmd = [
            "docker",
            "run",
            "--rm",
            "-it",
            "--env-file",
            ENV_FILE_PATH,
            image,
            "python",
            "tests/test_docker_environment.py",
        ]
        try:
            result = subprocess.run(cmd)
            sys.exit(result.returncode)
        except Exception as e:
            print(f"❌ Failed to run Docker environment verification: {e}")
            logger.error(
                f"Failed to run Docker environment verification: {e}", exc_info=True
            )
            sys.exit(1)


def docker_test_suite(suite_name: str, mode: str = "test") -> None:
    valid_suites = [
        "frontend",
        "backend",
        "integration",
        "comprehensive",
        "unit",
        "performance",
        "all",
        "demo",
    ]
    if suite_name not in valid_suites:
        print(f"❌ Unknown test suite: {suite_name}")
        print(
            "Available suites: frontend, backend, integration, unit, performance, demo, all, comprehensive"
        )
        sys.exit(1)
    print(f"🧪 Running test suite: {suite_name}")
    logger.info(f"Running test suite: {suite_name}")
    image_map = {
        "test": "nyp-fyp-chatbot-test",
        "prod": "nyp-fyp-chatbot-prod",
        "dev": "nyp-fyp-chatbot-dev",
    }
    image = image_map.get(mode, "nyp-fyp-chatbot-test")
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--env-file",
        ENV_FILE_PATH,
        image,
        "python",
        "tests/comprehensive_test_suite.py",
        "--suite",
        suite_name,
    ]
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Failed to run test suite {suite_name} in Docker: {e}")
        logger.error(
            f"Failed to run test suite {suite_name} in Docker: {e}", exc_info=True
        )
        sys.exit(1)


def docker_test_file(test_file: str, mode: str = "test") -> None:
    import pathlib

    test_path = pathlib.Path(test_file)
    if not test_path.exists():
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    print(f"🧪 Running test file: {test_file}")
    logger.info(f"Running test file: {test_file}")
    image_map = {
        "test": "nyp-fyp-chatbot-test",
        "prod": "nyp-fyp-chatbot-prod",
        "dev": "nyp-fyp-chatbot-dev",
    }
    image = image_map.get(mode, "nyp-fyp-chatbot-test")
    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--env-file",
        ENV_FILE_PATH,
        image,
        "python",
        test_file,
    ]
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Failed to run test file {test_file} in Docker: {e}")
        logger.error(
            f"Failed to run test file {test_file} in Docker: {e}", exc_info=True
        )
        sys.exit(1)


def list_available_tests():
    print("🧪 Available Tests and Suites")
    print("=" * 50)
    print("\n📋 Test Suites:")
    suites = {
        "frontend": "Frontend UI tests",
        "backend": "Backend API tests",
        "integration": "Integration tests",
        "comprehensive": "All tests organized by category",
        "unit": "Unit tests only",
        "performance": "Performance and optimization tests",
        "all": "Run all available tests",
        "demo": "Demo and interactive tests",
    }
    for suite, description in suites.items():
        print(f"  {suite:<15} - {description}")
    print("\n📄 Individual Test Files:")
    test_dirs = [
        "tests/frontend",
        "tests/backend",
        "tests/integration",
        "tests/performance",
        "tests/llm",
    ]
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            print(f"\n  📁 {test_dir}/")
            for file in sorted(os.listdir(test_dir)):
                if file.endswith(".py") and file.startswith("test_"):
                    print(f"    {file}")
    demo_dir = "tests/demos"
    if os.path.exists(demo_dir):
        print(f"\n  📁 {demo_dir}/")
        for file in sorted(os.listdir(demo_dir)):
            if file.endswith(".py") and file.startswith("demo_"):
                print(f"    {file}")
    print("\n💡 Usage Examples:")
    print("  python setup.py --docker-test-suite frontend")
    print("  python setup.py --docker-test-file tests/backend/test_backend.py")
    print("  python setup.py --docker-test  # Environment verification")
