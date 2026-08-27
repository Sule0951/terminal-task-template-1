# Execution model

How the parts of a task directory end up inside the container, and how the agent, the oracle, and the verifier interact with the environment. Read [`CONTEXT.md`](../CONTEXT.md) for the vocabulary first.

## The one rule that explains everything

**The agent is isolated.** While the agent works, the container holds only the environment. The `solution/` and `tests/` directories are *not* present — they are added later, and only for the phase that needs them:

- `solution/` appears only when the **oracle** runs (never during a real agent run).
- `tests/` appears only when the **verifier** runs.

That isolation is what makes the reward trustworthy: the agent can't read the oracle solution or the tests, so a passing reward means it actually solved the task.

## Repo directory → container path

Your task directory on disk maps into the container like this:

| In your repo | In the container | Present during | Who sees it |
|---|---|---|---|
| `environment/` (built by `Dockerfile`) | baked into the image, rooted at `WORKDIR` (e.g. `/app`) | every phase | agent, oracle, verifier |
| the agent's / oracle's edits | `WORKDIR` (e.g. `/app`) | created during the run, persists into the verifier | agent, oracle, verifier |
| `solution/` | `/solution` | oracle run only | oracle (never the agent) |
| `tests/` | `/tests` | verifier only | verifier (never the agent) |
| — | `/logs/verifier/reward.txt` | written by the verifier | Harbor (grades on it) |

The environment is **built once**; the agent phase (or oracle phase) and the verifier phase run in that **same container**, so files written to `WORKDIR` survive from one phase into the next.

## The lifecycle

A task is built once, then forks: the middle phase is *either* an agent run *or* an oracle run, and both feed into the **same** verifier.

```
BUILD ─▶ image built from environment/Dockerfile (WORKDIR /app)
   │
   ▼
MIDDLE PHASE — exactly one of:
   ├─ AGENT    works in /app; /solution and /tests absent;
   │           writes its solution into /app
   └─ ORACLE   /solution mounted; solve.sh writes the
               reference result into /app
   │
   ▼
VERIFIER   /tests added; test.sh runs the suite against /app;
           writes /logs/verifier/reward.txt (1 or 0)
```

- **Same container**: whichever middle phase runs, its files in `/app` persist into the verifier phase — the verifier grades real output, not a copy.
- **Same verifier**: the agent and the oracle are graded by identical code. Oracle validation (`./scripts/validate-task.sh`) is just "run the verifier against the reference result instead of an agent's." Reward `1` ⇒ the task is solvable and the verifier agrees; if the oracle can't earn `1`, no agent can.
- **Agent isolation**: `/solution` exists only in the oracle phase and `/tests` only in the verifier phase, so a real agent sees neither.

## Worked example: `hello-world-py`

The instruction asks the agent to create `/app/hello.txt` containing `Hello, Terminal Tasks!`.

**Environment** — `environment/Dockerfile` sets the stage and nothing more:

```dockerfile
FROM ubuntu:24.04
WORKDIR /app
```

**Oracle solution** — `solution/solve.sh` copies the reference file from `/solution` into `/app`:

```bash
cp /solution/hello.txt /app/hello.txt
```

Note the source is `/solution/hello.txt` (the mounted `solution/` dir) and the destination is `/app` (the shared `WORKDIR`). An agent, which never sees `/solution`, would instead write `/app/hello.txt` itself.

**Verifier** — `tests/test.sh` installs its own tooling, then checks `/app`:

```bash
uvx --python 3.12 --with pytest==8.4.1 pytest /tests/test_outputs.py   # reads /app/hello.txt, asserts content
# writes 1 or 0 to /logs/verifier/reward.txt
```

The test reads `/app/hello.txt` — the exact file the agent (or oracle) wrote — so it is always grading real output, not a copy.

**Filesystem at each phase** (`—` means the path isn't present yet):

| Container path | Oracle phase | Verifier phase |
|---|---|---|
| `/app/` | empty | `hello.txt` — written by `solve.sh` |
| `/solution/` | `hello.txt` — the reference file | — |
| `/tests/` | — | `test.sh`, `test_outputs.py` |
| `/logs/verifier/` | — | `reward.txt` → `1` |

## Where dependencies go

Because the agent image and the verifier share a container but serve different purposes, dependencies split by who needs them:

| Dependency | Goes in | Why |
|---|---|---|
| What the agent needs to solve the task (runtimes, app source, libraries) | `environment/Dockerfile` and `environment/` | Available while the agent works |
| Verifier-only tooling (bun, pytest, Playwright, browsers) | the setup section of `tests/test.sh` | Keeps the agent image lean and out of the agent's way |

See `tasks/hello-world-py/tests/test.sh` for the recommended pattern: setup output goes to `setup-stdout.txt`, suite output to `suite-stdout.txt`.
