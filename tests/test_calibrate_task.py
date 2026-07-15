import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CALIBRATE = ROOT / "scripts" / "calibrate-task.sh"
COMMIT = "d" * 40


class CalibrateTaskTests(unittest.TestCase):
    def test_runs_harbor_with_fixed_agent_model_and_eight_attempts(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        task_dir = temp_dir / "example-task"
        task_dir.mkdir()
        (task_dir / "task.toml").write_text('schema_version = "1.3"\n')
        jobs_dir = temp_dir / "jobs"
        bin_dir = temp_dir / "bin"
        bin_dir.mkdir()
        fake_harbor = bin_dir / "harbor"
        fake_harbor.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
[[ "$*" == *"-a terminus-2"* ]]
[[ "$*" == *"-m anthropic/claude-opus-4-8"* ]]
[[ "$*" == *"-k 8"* ]]
for i in {0..7}; do
  mkdir -p "$HARBOR_JOBS_DIR/run-$i/verifier"
  if [[ "$i" -lt 4 ]]; then echo 1; else echo 0; fi > "$HARBOR_JOBS_DIR/run-$i/verifier/reward.txt"
done
"""
        )
        fake_harbor.chmod(0o755)
        env_file = temp_dir / ".env"
        env_file.write_text("ANTHROPIC_API_KEY=test\n")
        environment = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "HARBOR_JOBS_DIR": str(jobs_dir),
        }

        result = subprocess.run(
            [
                "bash",
                str(CALIBRATE),
                str(task_dir),
                "--commit",
                COMMIT,
                "--env-file",
                str(env_file),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(
            (task_dir / "calibration" / "results.json").read_text()
        )
        self.assertEqual(record["commit"], COMMIT)
        self.assertEqual(record["success_count"], 4)
        self.assertTrue(record["accepted"])


if __name__ == "__main__":
    unittest.main()
