import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-task-metadata.py"
COMMIT = "a" * 40


class ValidateTaskMetadataTests(unittest.TestCase):
    def make_task(
        self,
        *,
        category: str = "Bug Fix",
        languages: list[str] | None = None,
        provenance: dict | None = None,
        attestation_commit: str = COMMIT,
        template_example: bool = False,
        with_attestation: bool = True,
    ) -> Path:
        task_dir = Path(tempfile.mkdtemp()) / "example-task"
        (task_dir / "attestations").mkdir(parents=True)
        language_values = languages if languages is not None else ["Python"]
        (task_dir / "task.toml").write_text(
            "\n".join(
                [
                    'schema_version = "1.3"',
                    "",
                    "[metadata]",
                    f'category = "{category}"',
                    "primary_languages = ["
                    + ", ".join(f'"{language}"' for language in language_values)
                    + "]",
                    f"template_example = {str(template_example).lower()}",
                    "",
                ]
            )
        )
        (task_dir / "provenance.json").write_text(
            json.dumps(
                provenance
                if provenance is not None
                else {
                    "schema_version": 1,
                    "third_party_material": [
                        {
                            "name": "pytest",
                            "source": "https://pypi.org/project/pytest/",
                            "license": "MIT",
                            "version_or_hash": "8.4.1",
                            "ai_training_authorization": "MIT permits this use.",
                        }
                    ],
                }
            )
        )
        if with_attestation:
            (task_dir / "attestations" / "jane-doe.md").write_text(
                f"""# Askable Task Contribution Attestation

Task: example-task
Commit: {attestation_commit}
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
        return task_dir

    def validate(self, task_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                "--task",
                str(task_dir),
                "--commit",
                COMMIT,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_accepts_complete_task_metadata(self) -> None:
        result = self.validate(self.make_task())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_unknown_category(self) -> None:
        result = self.validate(self.make_task(category="Documentation"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("category", result.stderr)

    def test_rejects_empty_primary_languages(self) -> None:
        result = self.validate(self.make_task(languages=[]))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("primary_languages", result.stderr)

    def test_rejects_incomplete_provenance_record(self) -> None:
        result = self.validate(
            self.make_task(
                provenance={
                    "schema_version": 1,
                    "third_party_material": [{"name": "pytest"}],
                }
            )
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("provenance", result.stderr)

    def test_rejects_attestation_for_a_different_commit(self) -> None:
        result = self.validate(self.make_task(attestation_commit="b" * 40))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("attestation", result.stderr)

    def test_accepts_template_example_without_contributor_attestation(self) -> None:
        result = self.validate(
            self.make_task(template_example=True, with_attestation=False)
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
