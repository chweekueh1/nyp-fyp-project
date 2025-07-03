#!/usr/bin/env bash
set -e

mkdir -p logs
LOGFILE=logs/test_results.log
> "$LOGFILE"

# Run environment check
python3 scripts/check_env.py
if [ $? -ne 0 ]; then
  echo "❌ Environment check failed. Aborting tests." | tee -a "$LOGFILE"
  exit 1
fi

# Determine chatbot directory using Python (same as backend)
CHATBOT_DIR=$(python3 -c 'from infra_utils import get_chatbot_dir; print(get_chatbot_dir())')
echo "🔍 Using chatbot directory: $CHATBOT_DIR" | tee -a "$LOGFILE"

ALL_PASSED=1
PASSED_TESTS=()
FAILED_TESTS=()

run_tests_in_dir() {
  DIR=$1
  for TESTFILE in $DIR/*.py; do
    if [[ -f "$TESTFILE" ]]; then
      echo -e "\n🧪 Running $TESTFILE in $CHATBOT_DIR..." | tee -a "$LOGFILE"
      if [ -d "$CHATBOT_DIR" ]; then
        (cd "$CHATBOT_DIR" && python3 "/app/$TESTFILE" >> "$LOGFILE" 2>&1)
      else
        echo "⚠️  Chatbot directory $CHATBOT_DIR does not exist. Running in current directory." | tee -a "$LOGFILE"
        python3 "$TESTFILE" >> "$LOGFILE" 2>&1
      fi
      if [ $? -eq 0 ]; then
        echo "✅ $TESTFILE PASSED" | tee -a "$LOGFILE"
        PASSED_TESTS+=("$TESTFILE")
      else
        echo "❌ $TESTFILE FAILED" | tee -a "$LOGFILE"
        FAILED_TESTS+=("$TESTFILE")
        ALL_PASSED=0
      fi
    fi
  done
}

run_tests_in_dir tests/frontend
run_tests_in_dir tests/backend
run_tests_in_dir tests/integration

# Summary
echo -e "\n==================== TEST SUMMARY ====================" | tee -a "$LOGFILE"
echo "PASSED TESTS:" | tee -a "$LOGFILE"
for t in "${PASSED_TESTS[@]}"; do
  echo "  ✅ $t" | tee -a "$LOGFILE"
done
echo "FAILED TESTS:" | tee -a "$LOGFILE"
for t in "${FAILED_TESTS[@]}"; do
  echo "  ❌ $t" | tee -a "$LOGFILE"
done

if [ $ALL_PASSED -eq 1 ]; then
  echo -e "\n🎉 All tests passed!" | tee -a "$LOGFILE"
  exit 0
else
  echo -e "\n💥 Some tests failed. See $LOGFILE for details." | tee -a "$LOGFILE"
  exit 1
fi
