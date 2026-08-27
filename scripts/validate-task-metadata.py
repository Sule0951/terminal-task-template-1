#!/usr/bin/env python3
"""Validate task classification, provenance, and contributor attestations."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


ALLOWED_CATEGORIES = {
    "Bug Fix",
    "Generation",
    "Feature Request",
    "Refactor",
    "Translation/Migration",
    "Decompilation/Reverse Engineering",
    "Security Patch/Exploitation",
}
PROVENANCE_FIELDS = {
    "name",
    "source",
    "license",
    "version_or_hash",
    "ai_training_authorization",
}
ATTESTATION_CHECKS = (
    "- [x] I hand-wrote the task instruction, or edited it so heavily that every requirement is my own; it was not pasted from an AI tool.",
    "- [x] I personally verified every file in this task — environment, tests, and reference solution — and can explain and defend each decision in a live walkthrough.",
    "- [x] I disclosed every AI tool used on this task in metadata.ai_tools_used in task.toml.",
    "- [x] I own or have authority to contribute all material in my contribution.",
    "- [x] I assign all right, title, and interest in my contribution to Askable.",
)


def is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def read_toml(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        with path.open("rb") as task_file:
            return tomllib.load(task_file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        errors.append(f"task.toml: {error}")
        return {}


def validate_metadata(task_dir: Path, errors: list[str]) -> bool:
    task_toml = task_dir / "task.toml"
    if not task_toml.is_file():
        errors.append("task.toml is missing")
        return False

    document = read_toml(task_toml, errors)
    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("task.toml must contain a [metadata] section")
        return False

    environment = document.get("environment")
    network_mode = (
        environment.get("network_mode") if isinstance(environment, dict) else None
    )
    if network_mode != "no-network" and not is_nonempty_string(
        metadata.get("network_justification")
    ):
        errors.append(
            'environment.network_mode must be "no-network"; any other value '
            "requires a non-empty metadata.network_justification explaining why "
            "the task cannot run offline"
        )

    category = metadata.get("category")
    if category not in ALLOWED_CATEGORIES:
        errors.append(
            "metadata.category must be one of: " + ", ".join(sorted(ALLOWED_CATEGORIES))
        )

    languages = metadata.get("primary_languages")
    if (
        not isinstance(languages, list)
        or not languages
        or not all(is_nonempty_string(language) for language in languages)
    ):
        errors.append(
            "metadata.primary_languages must be a non-empty list of language names"
        )

    dockerfile = task_dir / "environment" / "Dockerfile"
    if dockerfile.is_file():
        try:
            dockerfile_text = dockerfile.read_text()
        except OSError as error:
            errors.append(f"environment/Dockerfile: {error}")
            dockerfile_text = ""
        if (
            dockerfile_text
            and "git init" not in dockerfile_text
            and not is_nonempty_string(metadata.get("git_justification"))
        ):
            errors.append(
                "environment/Dockerfile must install git and create the initial "
                "baseline commit (see the template snippet), or "
                "metadata.git_justification must explain why git does not apply"
            )

    ai_tools = metadata.get("ai_tools_used")
    if ai_tools is not None and (
        not isinstance(ai_tools, list)
        or not all(is_nonempty_string(tool) for tool in ai_tools)
    ):
        errors.append("metadata.ai_tools_used must be a list of non-empty strings")
    return metadata.get("template_example") is True


def validate_provenance(task_dir: Path, errors: list[str]) -> None:
    provenance_path = task_dir / "provenance.json"
    try:
        provenance = json.loads(provenance_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"provenance.json: {error}")
        return

    if provenance.get("schema_version") != 1:
        errors.append("provenance.json schema_version must be 1")

    material = provenance.get("third_party_material")
    if not isinstance(material, list):
        errors.append("provenance.json third_party_material must be a list")
        return

    for index, item in enumerate(material):
        if not isinstance(item, dict):
            errors.append(f"provenance item {index} must be an object")
            continue
        for field in sorted(PROVENANCE_FIELDS):
            if not is_nonempty_string(item.get(field)):
                errors.append(
                    f"provenance item {index} is missing a non-empty {field}"
                )


def document_field(document: str, label: str) -> str | None:
    match = re.search(rf"^{re.escape(label)}:\s*(.+?)\s*$", document, re.MULTILINE)
    return match.group(1).strip() if match else None


def validate_attestations(task_dir: Path, commit: str, errors: list[str]) -> None:
    attestation_paths = sorted((task_dir / "attestations").glob("*.md"))
    if not attestation_paths:
        errors.append("attestations must contain at least one contributor document")
        return

    for attestation_path in attestation_paths:
        try:
            document = attestation_path.read_text()
        except OSError as error:
            errors.append(f"attestation {attestation_path.name}: {error}")
            continue

        attested_commit = document_field(document, "Commit")
        if commit == "UNCALIBRATED":
            # No calibration record yet (Askable runs the authoritative job).
            # The attestation must still bind to a real task-code commit.
            if not attested_commit or not re.fullmatch(
                r"[0-9a-f]{40}", attested_commit
            ):
                errors.append(
                    f"attestation {attestation_path.name} must bind to a "
                    "40-character task-code commit SHA"
                )
        elif attested_commit != commit:
            errors.append(
                f"attestation {attestation_path.name} must bind to commit {commit}"
            )
        if not is_nonempty_string(document_field(document, "Legal name")):
            errors.append(f"attestation {attestation_path.name} is missing Legal name")
        handle = document_field(document, "GitHub handle")
        if not handle or not handle.startswith("@"):
            errors.append(
                f"attestation {attestation_path.name} must include GitHub handle"
            )
        if not is_nonempty_string(document_field(document, "Date")):
            errors.append(f"attestation {attestation_path.name} is missing Date")
        if not is_nonempty_string(document_field(document, "Signature")):
            errors.append(f"attestation {attestation_path.name} is missing Signature")
        for required_check in ATTESTATION_CHECKS:
            if required_check not in document:
                errors.append(
                    f"attestation {attestation_path.name} is missing a required declaration"
                )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()

    errors: list[str] = []
    template_example = validate_metadata(args.task, errors)
    validate_provenance(args.task, errors)
    if not template_example:
        validate_attestations(args.task, args.commit, errors)

    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Metadata and attestations are valid for {args.task}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
