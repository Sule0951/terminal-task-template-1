# Terminal Task Template

Source-available template for creating [Harbor](https://www.harborframework.com/) /
[Terminal-Bench](https://www.tbench.ai/) tasks for Askable. It includes a complete
`hello-world` example, task scaffolding, deterministic oracle validation, and a
reproducible Claude Opus 4.8 calibration workflow.

Use is restricted by the repository license and the Askable participant agreement.
Do not use this repository to create tasks for another purpose.

## Before you start

1. Sign the Askable participant agreement.
2. Fork this repository and keep your task repository private.
3. Install [Docker](https://docs.docker.com/get-docker/),
   [uv](https://docs.astral.sh/uv/), and Harbor:

   ```bash
   uv tool install harbor
   ```

4. Read `CONTRIBUTING.md`, especially the human-authorship and provenance rules.

## Non-negotiable submission rules

- Task code must be human-written. AI is allowed for brainstorming and validation,
  but not for generating, translating, rewriting, or modifying task code,
  environments, verifiers, oracle solutions, scripts, or fixtures.
- Every contributor must submit a signed, commit-bound attestation assigning their
  contribution rights to Askable and warranting that they have authority to do so.
- Record every third-party dependency, code sample, dataset, binary, and fixture in
  `provenance.json`. Only include material whose license or permission supports
  Askable's intended AI-training use.
- Add Askable as a collaborator before requesting final verification.

Automated checks enforce the record formats. They cannot prove human authorship,
complete provenance, or ownership; those are enforced by the participant agreement
and Askable review.

## Create a task

```bash
./scripts/new-task.sh my-new-task
```

The generated task contains:

- `instruction.md` — the agent-facing task instruction
- `task.toml` — Harbor configuration, category, and primary languages
- `environment/Dockerfile` — the agent environment
- `tests/test.sh` — verifier entry point, which writes
  `/logs/verifier/reward.txt` or `reward.json`
- `solution/solve.sh` — reference solution for oracle validation
- `provenance.json` — third-party-material declarations
- `attestations/YOUR_GITHUB_HANDLE.md` — rights-assignment and human-authorship
  declaration

Set exactly one `metadata.category` in `task.toml`:

- `Bug Fix`
- `Generation`
- `Feature Request`
- `Refactor`
- `Translation/Migration`
- `Decompilation/Reverse Engineering`
- `Security Patch/Exploitation`

Set `metadata.primary_languages` to a non-empty list of the primary implementation
languages. Use `Python`, `Rust`, `TypeScript`, and similar conventional names.

`tasks/hello-world` is a working reference example only. It is deliberately easy
and is not eligible for submission.

## Develop and validate

Explore a task environment interactively:

```bash
harbor tasks start-env -p tasks/my-new-task -e docker -i
```

Validate its oracle solution:

```bash
./scripts/validate-task.sh tasks/my-new-task
```

The oracle runs `solution/solve.sh`, then the verifier. A reward of `1` means the
task is solvable and the verifier passes. Inspect failures with:

```bash
harbor view ./trials
```

Validate task metadata and submission records:

```bash
./scripts/validate-submissions.sh
```

## Calibrate difficulty

Eligible tasks must have Claude Opus 4.8 (`terminus-2`) succeed at least once but
no more than four times in eight attempts:

```text
1 <= successful trials <= 4
0.125 <= Pass@8 <= 0.5
```

Commit the task code and provenance first, then record that commit:

```bash
git add tasks/my-new-task
git commit -m "Add my new terminal task"
TASK_CODE_COMMIT="$(git rev-parse HEAD)"
```

Copy `.env.example` to `.env` and add your own `ANTHROPIC_API_KEY`. Complete every
contributor attestation using `TASK_CODE_COMMIT`, then run:

```bash
./scripts/calibrate-task.sh tasks/my-new-task \
  --commit "$TASK_CODE_COMMIT" \
  --env-file .env
```

The script always uses `terminus-2`, `anthropic/claude-opus-4-8`, and `-k 8`. It
writes `tasks/my-new-task/calibration/results.json` and rejects zero or five or
more successful trials. Inspect agent trajectories with:

```bash
harbor view ./jobs
```

Commit the calibration result and completed attestations in a second, immutable
submission commit. Provide both the submission commit SHA and `TASK_CODE_COMMIT`
to Askable. This two-commit flow avoids an impossible self-reference: a file inside
a Git commit cannot contain that same commit's SHA.

## Askable verification

Askable runs the trusted workflow template in
`verification/askable-verify-submission.yml` from an Askable-controlled repository,
not from your private fork. It checks out the submitted SHA, reruns oracle
validation and all eight Opus attempts with Askable-held credentials, hashes the
task content, and emits a signed provenance attestation.

Do not add Askable secrets to a participant-owned repository or workflow.

## Quality checklist

- [ ] The instruction is unambiguous and tests verify only its stated behavior.
- [ ] `task.toml` has an approved category and non-empty primary-language list.
- [ ] Oracle validation earns reward `1`.
- [ ] `provenance.json` accounts for every third-party material item.
- [ ] Every contributor has completed an attestation.
- [ ] The task earns 1–4 successes from eight Opus 4.8 attempts.
- [ ] Dockerfile installs only agent dependencies; verifier dependencies stay in
  `tests/test.sh`.
- [ ] No secrets are committed and network access is declared explicitly.

## Local template checks

```bash
python3 -m unittest discover -s tests -v
./scripts/validate-submissions.sh
./scripts/validate-all.sh
```

## Reference

- [Harbor task structure](https://www.harborframework.com/docs/tasks)
- [Harbor task tutorial](https://www.harborframework.com/docs/tasks/task-tutorial)
- [Terminal-Bench](https://www.tbench.ai/)
