"""
Bootstrap Test Runner for NYP FYP Chatbot

This script runs environment checks and then executes all frontend, backend, and integration tests, summarizing results for CI and local development.
"""

#!/usr/bin/env python3
import os
import sys
import subprocess
import glob
from infra_utils import get_chatbot_dir

# Run environment check
result = subprocess.run([sys.executable, "scripts/check_env.py"])
if result.returncode != 0:
    print("❌ Environment check failed. Aborting tests.")
    sys.exit(1)

CHATBOT_DIR = get_chatbot_dir()
print(f"🔍 Using chatbot directory: {CHATBOT_DIR}")

ALL_PASSED = True
PASSED_TESTS = []
FAILED_TESTS = []


def run_tests_in_dir(directory):
    for testfile in glob.glob(os.path.join(directory, "*.py")):
        print(f"\n🧪 Running {testfile} in {CHATBOT_DIR}...")
        if os.path.isdir(CHATBOT_DIR):
            result = subprocess.run(
                [sys.executable, os.path.abspath(testfile)],
                cwd=CHATBOT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        else:
            print(
                f"⚠️  Chatbot directory {CHATBOT_DIR} does not exist. Running in current directory."
            )
            result = subprocess.run(
                [sys.executable, os.path.abspath(testfile)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        print(result.stdout.decode())
        if result.returncode == 0:
            print(f"✅ {testfile} PASSED")
            PASSED_TESTS.append(testfile)
        else:
            print(f"❌ {testfile} FAILED")
            FAILED_TESTS.append(testfile)
            global ALL_PASSED
            ALL_PASSED = False


run_tests_in_dir("tests/frontend")
run_tests_in_dir("tests/backend")
run_tests_in_dir("tests/integration")

print("\n==================== TEST SUMMARY ====================")
print("PASSED TESTS:")
for t in PASSED_TESTS:
    print(f"  ✅ {t}")
print("FAILED TESTS:")
for t in FAILED_TESTS:
    print(f"  ❌ {t}")

if ALL_PASSED:
    print("\n🎉 All tests passed!")
    sys.exit(0)
else:
    print("\n💥 Some tests failed.")
    sys.exit(1)
