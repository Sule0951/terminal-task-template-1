#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

require_command harbor
require_command docker

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <task-path>" >&2
  exit 1
fi

TASK_PATH="$1"

if [[ ! -d "$TASK_PATH" ]]; then
  echo "Error: task directory not found: $TASK_PATH" >&2
  exit 1
fi

if [[ ! -f "$TASK_PATH/task.toml" ]]; then
  echo "Error: missing task.toml in $TASK_PATH" >&2
  exit 1
fi

echo "Validating task: $TASK_PATH"
harbor trials start -p "$TASK_PATH" -a oracle

TRIAL_DIR="$(find ./trials -mindepth 1 -maxdepth 1 -type d -print 2>/dev/null | sort | tail -n 1 || true)"

if [[ -z "$TRIAL_DIR" ]]; then
  echo "Error: no trial output found under ./trials" >&2
  exit 1
fi

REWARD_FILE="$TRIAL_DIR/verifier/reward.txt"
if [[ ! -f "$REWARD_FILE" ]]; then
  REWARD_FILE="$TRIAL_DIR/verifier/reward.json"
fi

if [[ ! -f "$REWARD_FILE" ]]; then
  echo "Error: reward file not found in $TRIAL_DIR/verifier/" >&2
  echo "Inspect with: harbor view ./trials" >&2
  exit 1
fi

if [[ "$REWARD_FILE" == *.json ]]; then
  REWARD="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['reward'])" "$REWARD_FILE")"
else
  REWARD="$(tr -d '[:space:]' < "$REWARD_FILE")"
fi

if [[ "$REWARD" != "1" && "$REWARD" != "1.0" ]]; then
  echo "Error: oracle validation failed (reward=$REWARD, expected 1)" >&2
  echo "Inspect with: harbor view ./trials" >&2
  exit 1
fi

echo "OK: $TASK_PATH (reward=1)"
