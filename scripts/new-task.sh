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
  echo "Usage: $0 <task-name>" >&2
  exit 1
fi

TASK_NAME="$1"

harbor tasks init "$TASK_NAME" \
  -p tasks/ \
  --metadata-template templates/askable-task.toml \
  --include-canary-strings

TASK_DIR="tasks/${TASK_NAME}"
mkdir -p "$TASK_DIR/attestations"
cat > "$TASK_DIR/provenance.json" <<'EOF'
{
  "schema_version": 1,
  "third_party_material": []
}
EOF
sed "s/TASK_NAME/${TASK_NAME}/g" templates/contributor-attestation.md \
  > "$TASK_DIR/attestations/YOUR_GITHUB_HANDLE.md"

echo ""
echo "Created ${TASK_DIR}/"
echo "Next steps:"
echo "  1. Edit tasks/${TASK_NAME}/instruction.md"
echo "  2. Update tasks/${TASK_NAME}/task.toml (name, description, category, languages)"
echo "  3. Complete provenance.json and the contributor attestation."
echo "  4. Edit tasks/${TASK_NAME}/environment/Dockerfile, tests/, and solution/"
echo "  5. Run ./scripts/validate-task.sh tasks/${TASK_NAME}"
