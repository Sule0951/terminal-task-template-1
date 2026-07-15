import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARIZER = ROOT / "scripts" / "summarize-calibration.py"
COMMIT = "c" * 40


class SummarizeCalibrationTests(unittest.TestCase):
    def summarize(self, rewards: list[int]) -> tuple[subprocess.CompletedProcess[str], Path]:
        temp_dir = Path(tempfile.mkdtemp())
        rewards_file = temp_dir / "rewards.json"
        output_file = temp_dir / "results.json"
        rewards_file.write_text(json.dumps({"rewards": rewards}))
        result = subprocess.run(
            [
                sys.executable,
                str(SUMMARIZER),
                "--task",
                "example-task",
                "--commit",
                COMMIT,
                "--rewards-file",
                str(rewards_file),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result, output_file

    def test_accepts_four_successes_from_eight_attempts(self) -> None:
        result, output_file = self.summarize([1, 1, 1, 1, 0, 0, 0, 0])
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(output_file.read_text())
        self.assertEqual(record["success_count"], 4)
        self.assertEqual(record["pass_at_8"], 0.5)
        self.assertTrue(record["accepted"])

    def test_rejects_zero_successes(self) -> None:
        result, output_file = self.summarize([0] * 8)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(output_file.exists(), result.stderr)
        self.assertFalse(json.loads(output_file.read_text())["accepted"])

    def test_rejects_five_successes(self) -> None:
        result, output_file = self.summarize([1] * 5 + [0] * 3)
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(output_file.exists(), result.stderr)
        self.assertFalse(json.loads(output_file.read_text())["accepted"])

    def test_rejects_anything_other_than_eight_rewards(self) -> None:
        result, output_file = self.summarize([1] * 4)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output_file.exists())


if __name__ == "__main__":
    unittest.main()
