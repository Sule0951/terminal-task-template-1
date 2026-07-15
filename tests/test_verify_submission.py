import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "verify-submission.sh"
COMMIT = "e" * 40


class VerifySubmissionTests(unittest.TestCase):
    def test_rejects_task_path_outside_candidate_checkout(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        candidate = temp_dir / "candidate"
        (candidate / ".git").mkdir(parents=True)
        env_file = temp_dir / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=test\n")

        result = subprocess.run(
            [
                "bash",
                str(VERIFY),
                "--candidate-dir",
                str(candidate),
                "--task",
                "../outside",
                "--submission-commit",
                COMMIT,
                "--task-code-commit",
                COMMIT,
                "--env-file",
                str(env_file),
                "--attestation-output",
                str(temp_dir / "attestation.json"),
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=ROOT,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task path must stay", result.stderr)

    def test_verifies_candidate_and_writes_attestation(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        candidate = temp_dir / "candidate"
        task_dir = candidate / "tasks" / "example-task"
        (candidate / ".git").mkdir(parents=True)
        (task_dir / "attestations").mkdir(parents=True)
        (task_dir / "task.toml").write_text(
            """schema_version = "1.3"

[metadata]
category = "Bug Fix"
primary_languages = ["Python"]
"""
        )
        (task_dir / "provenance.json").write_text(
            json.dumps({"schema_version": 1, "third_party_material": []})
        )
        (task_dir / "attestations" / "jane.md").write_text(
            f"""# Askable Task Contribution Attestation

Task: example-task
Commit: {COMMIT}
Legal name: Jane Doe
GitHub handle: @janedoe
Date: 2026-07-15

## Declarations

- [x] I did not use AI to generate, translate, rewrite, or modify task code.
- [x] I own or have authority to contribute all material in my contribution.
- [x] I assign all right, title, and interest in my contribution to Askable.

Signature: Jane Doe
"""
        )
        (task_dir / "environment").mkdir()
        (task_dir / "tests").mkdir()
        (task_dir / "solution").mkdir()
        (task_dir / "tests" / "test.sh").write_text("#!/usr/bin/env bash\n")
        (task_dir / "solution" / "solve.sh").write_text("#!/usr/bin/env bash\n")
        env_file = temp_dir / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=test\n")
        output = temp_dir / "attestation.json"
        bin_dir = temp_dir / "bin"
        bin_dir.mkdir()
        (bin_dir / "git").write_text(
            f"""#!/usr/bin/env bash
if [[ "$*" == *"rev-parse HEAD"* ]]; then
  echo "{COMMIT}"
else
  /usr/bin/git "$@"
fi
"""
        )
        (bin_dir / "harbor").write_text(
            f"""#!/usr/bin/env bash
set -euo pipefail
if [[ "$1 $2" == "trials start" ]]; then
  mkdir -p "{ROOT}/trials/trial/verifier"
  echo 1 > "{ROOT}/trials/trial/verifier/reward.txt"
else
  for i in {{0..7}}; do
    mkdir -p "$HARBOR_JOBS_DIR/run-$i/verifier"
    if [[ "$i" -lt 4 ]]; then echo 1; else echo 0; fi > "$HARBOR_JOBS_DIR/run-$i/verifier/reward.txt"
  done
fi
"""
        )
        for executable in bin_dir.iterdir():
            executable.chmod(0o755)
        jobs_dir = temp_dir / "jobs"
        environment = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "HARBOR_JOBS_DIR": str(jobs_dir),
        }
        try:
            result = subprocess.run(
                [
                    "bash",
                    str(VERIFY),
                    "--candidate-dir",
                    str(candidate),
                    "--task",
                    "tasks/example-task",
                "--submission-commit",
                COMMIT,
                "--task-code-commit",
                    COMMIT,
                    "--env-file",
                    str(env_file),
                    "--attestation-output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                check=False,
                cwd=ROOT,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            attestation = json.loads(output.read_text())
            self.assertEqual(attestation["commit"], COMMIT)
            self.assertEqual(attestation["task_code_commit"], COMMIT)
            self.assertEqual(attestation["success_count"], 4)
            self.assertTrue(attestation["oracle_validated"])
        finally:
            shutil.rmtree(ROOT / "trials", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
