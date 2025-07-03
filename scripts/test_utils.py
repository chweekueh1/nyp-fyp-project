import os
import sys
import subprocess
from typing import Optional
from infra_utils import setup_logging
from docker_utils import ensure_test_docker_image
from env_utils import running_in_docker

logger = setup_logging()

if os.name == "nt":
    LOCAL_VENV_PATH = os.path.expanduser(r"~/.nypai-chatbot/venv")
    LOCAL_VENV_PATH = os.path.expanduser(os.path.join("~", ".nypai-chatbot", "venv"))
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "Scripts", "python.exe")
else:
    LOCAL_VENV_PATH = os.path.expanduser("~/.nypai-chatbot/venv")
    VENV_PYTHON = os.path.join(LOCAL_VENV_PATH, "bin", "python")
DOCKER_VENV_PATH = "/home/appuser/.nypai-chatbot/venv"
DOCKER_VENV_PYTHON = os.path.join(DOCKER_VENV_PATH, "bin", "python")

ENV_FILE_PATH = os.environ.get("DOCKER_ENV_FILE", ".env")


def docker_test(test_target: Optional[str] = None) -> None:
    ensure_test_docker_image()
    print("🐳 [DEBUG] Dockerfile installs venv at: /home/appuser/.nypai-chatbot/venv")
    print(
        f"🐳 [DEBUG] Docker container will load environment variables from: {ENV_FILE_PATH} (via --env-file)"
    )
    print("🔍 Running environment check (scripts/check_env.py) before tests...")
    if running_in_docker():
        python_exe = "/home/appuser/.nypai-chatbot/venv/bin/python"
    else:
        python_exe = VENV_PYTHON
    env_check_result = subprocess.run([python_exe, "scripts/check_env.py"])
    if env_check_result.returncode != 0:
        print("❌ Environment check failed. Aborting tests.")
        sys.exit(1)
    else:
        print("✅ Environment check passed.")
    if test_target:
        print(f"🧪 Running {test_target} in test Docker container...")
        logger.info(f"Running {test_target} inside test Docker container.")
        if test_target == "all":
            print(
                "🚀 Running all tests using scripts/bootstrap_tests.sh for full integration..."
            )
            bootstrap_result = subprocess.run(["bash", "scripts/bootstrap_tests.sh"])
            if bootstrap_result.returncode == 0:
                print("✅ All tests passed via bootstrap_tests.sh.")
                sys.exit(0)
            else:
                print(
                    "❌ Some tests failed via bootstrap_tests.sh. See logs/test_results.log for details."
                )
                sys.exit(1)
        elif test_target.startswith("tests/") and test_target.endswith(".py"):
            result = subprocess.run(
                ["/home/appuser/.nypai-chatbot/venv/bin/python", test_target]
            )
            sys.exit(result.returncode)
        else:
            result = subprocess.run(
                [
                    "/home/appuser/.nypai-chatbot/venv/bin/python",
                    "tests/comprehensive_test_suite.py",
                    "--suite",
                    test_target,
                ]
            )
            sys.exit(result.returncode)
    else:
        print("🧪 Running Docker environment verification...")
        logger.info("Running Docker environment verification.")
        result = subprocess.run(
            [
                "/home/appuser/.nypai-chatbot/venv/bin/python",
                "tests/test_docker_environment.py",
            ]
        )
        sys.exit(result.returncode)


def docker_test_suite(suite_name: str) -> None:
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
    cmd = [
        "/home/appuser/.nypai-chatbot/venv/bin/python",
        "tests/comprehensive_test_suite.py",
    ]
    if suite_name in ["all", "comprehensive"]:
        pass
    else:
        cmd += ["--suite", suite_name]
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Failed to run test suite {suite_name}: {e}")
        logger.error(f"Failed to run test suite {suite_name}: {e}", exc_info=True)
        sys.exit(1)


def docker_test_file(test_file: str) -> None:
    import pathlib

    test_path = pathlib.Path(test_file)
    if not test_path.exists():
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    print(f"🧪 Running test file: {test_file}")
    logger.info(f"Running test file: {test_file}")
    cmd = ["/home/appuser/.nypai-chatbot/venv/bin/python", test_file]
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except Exception as e:
        print(f"❌ Failed to run test file {test_file}: {e}")
        logger.error(f"Failed to run test file {test_file}: {e}", exc_info=True)
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
