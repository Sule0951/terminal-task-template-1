#!/bin/bash

VERIFIER_DIR="/logs/verifier"

# --- Setup ---
# Install verifier-only dependencies. Keep agent image lean; put tooling here.
# Output goes to setup-stdout.txt so it stays separate from test results.
{
  apt-get update
  apt-get install -y curl
  curl -LsSf https://astral.sh/uv/0.9.5/install.sh | sh
  source "$HOME/.local/bin/env"
} >>"$VERIFIER_DIR/setup-stdout.txt" 2>&1

# --- Run test suite ---
# Disable errexit so a failing suite still lets us write reward.txt.
# Suite output goes to suite-stdout.txt (not Harbor's combined test-stdout.txt).
set +e
{
  uvx \
  --python 3.12 \
  --with pytest==8.4.1 \
  pytest /tests/test_outputs.py
} >>"$VERIFIER_DIR/suite-stdout.txt" 2>&1
TEST_EXIT=$?
set -e

# --- Write reward from suite exit code ---
# Harbor grades on reward.txt (1 = pass, 0 = fail). Do not change the exit
# status of this script based on TEST_EXIT; only the reward file matters.
if [ $TEST_EXIT -eq 0 ]; then
  echo 1 >"$VERIFIER_DIR/reward.txt"
else
  echo 0 >"$VERIFIER_DIR/reward.txt"
fi
