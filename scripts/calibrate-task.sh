#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JOBS_DIR="${HARBOR_JOBS_DIR:-$ROOT_DIR/jobs}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

usage() {
  echo "Usage: $0 <task-path> --commit <task-code-commit> [--env-file <path>]" >&2
  exit 1
}

TASK_PATH="${1:-}"
[[ -n "$TASK_PATH" ]] || usage
shift

COMMIT=""
ENV_FILE="$ROOT_DIR/.env"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --commit)
      COMMIT="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

[[ -n "$COMMIT" ]] || usage
[[ -f "$TASK_PATH/task.toml" ]] || {
  echo "Error: missing task.toml in $TASK_PATH" >&2
  exit 1
}
[[ -f "$ENV_FILE" ]] || {
  echo "Error: environment file not found: $ENV_FILE" >&2
  exit 1
}

require_command harbor
require_command python3

mkdir -p "$JOBS_DIR"
SNAPSHOT_FILE="$(mktemp)"
REWARDS_FILE="$(mktemp)"
trap 'rm -f "$SNAPSHOT_FILE" "$REWARDS_FILE"' EXIT

python3 "$ROOT_DIR/scripts/collect-calibration-rewards.py" \
  --jobs-dir "$JOBS_DIR" \
  --snapshot-out "$SNAPSHOT_FILE"

harbor run \
  -p "$TASK_PATH" \
  -a terminus-2 \
  -m anthropic/claude-opus-4-8 \
  -k 8 \
  --env-file "$ENV_FILE"

python3 "$ROOT_DIR/scripts/collect-calibration-rewards.py" \
  --jobs-dir "$JOBS_DIR" \
  --snapshot "$SNAPSHOT_FILE" \
  --output "$REWARDS_FILE"

python3 "$ROOT_DIR/scripts/summarize-calibration.py" \
  --task "$(basename "$TASK_PATH")" \
  --commit "$COMMIT" \
  --rewards-file "$REWARDS_FILE" \
  --output "$TASK_PATH/calibration/results.json"
