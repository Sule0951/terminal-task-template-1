#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  echo "Usage: $0 --candidate-dir <path> --task <relative-path> --submission-commit <sha> --task-code-commit <sha> --env-file <path> --attestation-output <path>" >&2
  exit 1
}

CANDIDATE_DIR=""
TASK_RELATIVE_PATH=""
SUBMISSION_COMMIT=""
TASK_CODE_COMMIT=""
ENV_FILE=""
ATTESTATION_OUTPUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --candidate-dir)
      CANDIDATE_DIR="${2:-}"
      shift 2
      ;;
    --task)
      TASK_RELATIVE_PATH="${2:-}"
      shift 2
      ;;
    --submission-commit)
      SUBMISSION_COMMIT="${2:-}"
      shift 2
      ;;
    --task-code-commit)
      TASK_CODE_COMMIT="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --attestation-output)
      ATTESTATION_OUTPUT="${2:-}"
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

[[ -n "$CANDIDATE_DIR" && -n "$TASK_RELATIVE_PATH" && -n "$SUBMISSION_COMMIT" && -n "$TASK_CODE_COMMIT" && -n "$ENV_FILE" && -n "$ATTESTATION_OUTPUT" ]] || usage
[[ "$TASK_RELATIVE_PATH" != /* && "$TASK_RELATIVE_PATH" != *".."* ]] || {
  echo "Error: task path must stay within the candidate checkout" >&2
  exit 1
}
[[ -d "$CANDIDATE_DIR/.git" ]] || {
  echo "Error: candidate directory must be a Git checkout" >&2
  exit 1
}
[[ -f "$ENV_FILE" ]] || {
  echo "Error: environment file not found: $ENV_FILE" >&2
  exit 1
}

ACTUAL_COMMIT="$(git -C "$CANDIDATE_DIR" rev-parse HEAD)"
[[ "$ACTUAL_COMMIT" == "$SUBMISSION_COMMIT" ]] || {
  echo "Error: candidate checkout is $ACTUAL_COMMIT, expected $SUBMISSION_COMMIT" >&2
  exit 1
}

TASK_DIR="$CANDIDATE_DIR/$TASK_RELATIVE_PATH"
[[ -f "$TASK_DIR/task.toml" ]] || {
  echo "Error: task directory is invalid: $TASK_DIR" >&2
  exit 1
}

python3 "$ROOT_DIR/scripts/validate-task-metadata.py" \
  --task "$TASK_DIR" \
  --commit "$TASK_CODE_COMMIT"
"$ROOT_DIR/scripts/validate-task.sh" "$TASK_DIR"
"$ROOT_DIR/scripts/calibrate-task.sh" "$TASK_DIR" \
  --commit "$TASK_CODE_COMMIT" \
  --env-file "$ENV_FILE"

python3 - "$TASK_DIR" "$TASK_RELATIVE_PATH" "$SUBMISSION_COMMIT" "$TASK_CODE_COMMIT" "$ATTESTATION_OUTPUT" <<'PY'
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

task_dir = Path(sys.argv[1])
task_path = sys.argv[2]
submission_commit = sys.argv[3]
task_code_commit = sys.argv[4]
output = Path(sys.argv[5])

digest = hashlib.sha256()
for path in sorted(file for file in task_dir.rglob("*") if file.is_file()):
    relative_path = path.relative_to(task_dir).as_posix().encode()
    digest.update(len(relative_path).to_bytes(8, "big"))
    digest.update(relative_path)
    content = path.read_bytes()
    digest.update(len(content).to_bytes(8, "big"))
    digest.update(content)

calibration = json.loads((task_dir / "calibration" / "results.json").read_text())
attestation = {
    "schema_version": 1,
    "task": task_path,
    "commit": submission_commit,
    "task_code_commit": task_code_commit,
    "task_content_sha256": digest.hexdigest(),
    "oracle_validated": True,
    "agent": calibration["agent"],
    "model": calibration["model"],
    "rewards": calibration["rewards"],
    "success_count": calibration["success_count"],
    "pass_at_8": calibration["pass_at_8"],
    "verified_at": datetime.now(timezone.utc).isoformat(),
}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(attestation, indent=2) + "\n")
PY
