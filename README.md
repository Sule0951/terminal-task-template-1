# Terminal Task Template

Source-available template for creating [Harbor](https://www.harborframework.com/) / [Terminal-Bench](https://www.tbench.ai/) tasks for Askable. It includes a complete `hello-world` example, task scaffolding, deterministic oracle validation, and a reproducible Claude Opus 4.8 calibration workflow.

Use is restricted by the repository license and the Askable participant agreement. Do not use this repository to create tasks for another purpose.

**New here?** Read `[CONTEXT.md](CONTEXT.md)` first — it defines the core concepts (task, environment, verifier, reward, oracle, calibration) that the rest of this guide assumes.

## Before you start

1. Sign the Askable participant agreement.
2. Fork this repository and keep your task repository private.
3. Install [Docker](https://docs.docker.com/get-docker/), [uv](https://docs.astral.sh/uv/), and Harbor:
  ```bash
   uv tool install harbor
  ```
4. Read `CONTRIBUTING.md`, especially the human-authorship and provenance rules.



## Non-negotiable submission rules

- Task code must be human-written. AI is allowed for brainstorming and validation, but not for generating, translating, rewriting, or modifying task code, environments, verifiers, oracle solutions, scripts, or fixtures.
- Every contributor must submit a signed, commit-bound attestation assigning their contribution rights to Askable and warranting that they have authority to do so.
- Record every third-party dependency, code sample, dataset, binary, and fixture in `provenance.json`. Only include material whose license or permission supports Askable's intended AI-training use.

Automated checks enforce the record formats. They cannot prove human authorship, complete provenance, or ownership; those are enforced by the participant agreement.

## Create a task

```bash
./scripts/new-task.sh my-new-task
```

The generated task contains the files defined in `[CONTEXT.md](CONTEXT.md)`:

- `instruction.md`
- `task.toml` — Harbor configuration
- `environment/Dockerfile`
- `tests/test.sh` — verifier entry point (writes `/logs/verifier/reward.txt` or `reward.json`)
- `solution/solve.sh` — the oracle solution
- `provenance.json`
- `attestations/YOUR_GITHUB_HANDLE.md`

Set exactly one approved `metadata.category` in `task.toml` (see the category list in `[CONTEXT.md](CONTEXT.md)`), and set `metadata.primary_languages` to a non-empty list of the primary implementation languages (`Python`, `Rust`, `TypeScript`, and similar conventional names).

`tasks/hello-world` is a working reference example only. It is deliberately easy and is not eligible for submission.

## Develop and validate



### How a task runs

The `solution/` and `tests/` directories don't sit next to the agent — they're isolated and appear only for the oracle and verifier phases. `[docs/execution-model.md](docs/execution-model.md)` explains, with diagrams and a `hello-world` walkthrough, how these directories map into the container, why the agent never sees them, and where each dependency belongs.

### Oracle validation

Validate the reference solution:

```bash
./scripts/validate-task.sh tasks/my-new-task
```

This runs the oracle then the verifier (see `[docs/execution-model.md](docs/execution-model.md)`); a reward of `1` means the task is solvable.

On failure, the script prints `cat` commands for the relevant trial logs under `./trials/<trial-name>/`:

- `verifier/setup-stdout.txt` — verifier dependency install output
- `verifier/suite-stdout.txt` — test suite output (pass/fail details)
- `agent/oracle.txt` — reference solution output (useful when `solve.sh` failed or did nothing)

`harbor view ./trials` is mainly useful for agent calibration runs, not oracle validation (oracle trials have no agent trajectory to browse).

### Interactive development

Explore a task environment interactively:

```bash
harbor tasks start-env -p tasks/my-new-task -e docker -i
```



### Submission record checks

Validate task metadata and submission records:

```bash
./scripts/validate-submissions.sh
```



## Calibrate difficulty

Once your oracle passes, so you know the task is solvable. Calibration now checks it's the *right* difficulty for Claude Opus 4.8 (`terminus-2`) — hard enough to be interesting, but not impossible.

1. Read `[CONTRIBUTING.md](CONTRIBUTING.md)` and fill out `provenance.json` for the task.
2. Commit the task code and provenance, then capture that commit's SHA:
  ```bash
   git add tasks/my-new-task
   git commit -m "Add my new terminal task"
   TASK_CODE_COMMIT="$(git rev-parse HEAD)"  # SHA of the commit just made; attestations bind to it
  ```
3. Copy `.env.example` to `.env` and add your own `ANTHROPIC_API_KEY`.
4. Complete each contributor attestation in `tasks/my-new-task/attestations/YOUR_GITHUB_HANDLE.md` using `TASK_CODE_COMMIT`,
5. Run the calibration:
  ```bash
   ./scripts/calibrate-task.sh tasks/my-new-task \
     --commit "$TASK_CODE_COMMIT" \
     --env-file .env
  ```
   The script always uses `terminus-2`, `anthropic/claude-opus-4-8`, and `-k 8`, and writes `tasks/my-new-task/calibration/results.json`. The task is eligible only if Opus 4.8 succeeds 1–4 times out of 8:
   Zero or five-plus successes are rejected. Inspect agent trajectories with `harbor view ./jobs`.
6. Commit the calibration result and completed attestations in a second, immutable submission commit:
  ```bash
   git add tasks/my-new-task/calibration tasks/my-new-task/attestations
   git commit -m "Add calibration results and attestations for my-new-task"
  ```
   Keep all required task files and both commits in your private repository. This two-commit flow avoids an impossible self-reference: a file inside a Git commit cannot contain that same commit's SHA.



## Quality checklist

- [ ] The instruction is unambiguous and tests verify only its stated behavior.
- [ ] `task.toml` has an approved category and non-empty primary-language list.
- [ ] Oracle validation earns reward `1`.
- [ ] `provenance.json` accounts for every third-party material item.
- [ ] Every contributor has completed an attestation.
- [ ] The task earns 1–4 successes from eight Opus 4.8 attempts.
- [ ] Dockerfile installs only agent dependencies; verifier dependencies stay in `tests/test.sh`.
- [ ] No secrets are committed and network access is declared explicitly.



## Local template checks

```bash
python3 -m unittest discover -s tests -v
./scripts/validate-submissions.sh
./scripts/validate-all.sh
```



## Reference

- `[CONTEXT.md](CONTEXT.md)` — core concepts and vocabulary
- `[docs/execution-model.md](docs/execution-model.md)` — how `solution/`, `tests/`, and the agent's work interact with the environment
- [Harbor task structure](https://www.harborframework.com/docs/tasks)
- [Harbor task tutorial](https://www.harborframework.com/docs/tasks/task-tutorial)
- [Terminal-Bench](https://www.tbench.ai/)

