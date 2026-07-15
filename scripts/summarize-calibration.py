#!/usr/bin/env python3
"""Create a reproducible Pass@8 calibration record from verifier rewards."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ATTEMPT_COUNT = 8
MODEL = "anthropic/claude-opus-4-8"
AGENT = "terminus-2"


def load_rewards(path: Path) -> list[int]:
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"could not read rewards file: {error}") from error

    rewards = payload.get("rewards") if isinstance(payload, dict) else None
    if not isinstance(rewards, list) or len(rewards) != ATTEMPT_COUNT:
        raise ValueError(f"expected exactly {ATTEMPT_COUNT} rewards")
    if any(reward not in (0, 1) for reward in rewards):
        raise ValueError("rewards must be binary 0 or 1 values")
    return rewards


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--rewards-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        rewards = load_rewards(args.rewards_file)
    except ValueError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    success_count = sum(rewards)
    pass_at_8 = success_count / ATTEMPT_COUNT
    accepted = 1 <= success_count <= 4
    record = {
        "schema_version": 1,
        "task": args.task,
        "commit": args.commit,
        "agent": AGENT,
        "model": MODEL,
        "attempt_count": ATTEMPT_COUNT,
        "rewards": rewards,
        "success_count": success_count,
        "pass_at_8": pass_at_8,
        "accepted": accepted,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n")

    if not accepted:
        print(
            "Error: calibration requires 1–4 successful trials out of 8",
            file=sys.stderr,
        )
        return 1

    print(
        f"Accepted: {success_count}/8 successes (Pass@8={pass_at_8:.3f})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
