# Difficulty Standard

This is Askable's acceptance bar for task difficulty. It overrides any looser difficulty language elsewhere in this repository. `AUTHORING.md` explains how to design to it.

## How difficulty is measured

Each frozen task is run **10 times** by the designated calibration agent and model — currently `terminus-2` with `google/gemini-3.6-flash`, as pinned in `calibration-target.json`. The number of passing attempts out of 10 is the task's difficulty measurement.

## The acceptance distribution

Across a delivered set of tasks:

| Passing attempts out of 10 | Share of delivered tasks |
|---|---|
| 0–4 | ≥ 80% |
| 5–6 | ≤ 20% |
| 7–10 | **0% — automatic rejection** |

The distribution applies at both the task level and the dataset level. A single task landing at 7+ is rejected no matter how well it is built.

## Eligibility band for an individual task

`calibration-target.json` sets the per-task band: **1–4 successes out of 10**.

- A task at 5–6 consumes scarce allowance and is usually returned for deepening.
- A task at **0/10 is not accepted automatically** — it is held for human review, because a task the model never solves may be broken or unfair rather than hard.

## Design for ~2 passes in 10 — and mind the noise

Ten attempts is a small sample. A task whose *true* pass rate is 50% has roughly a **1-in-6 chance of observing 7+ passes** and being auto-rejected, and a better-than-even chance of landing in the 5–6 band. The safe target is a true pass rate around **0.20–0.25** — the model genuinely solves it about 2 attempts in 10. At that level, auto-rejection risk is under 1% and the 5–6 band stays what it should be: buffer for sampling noise, not something you spend.

Practical reading: if your local agent runs (see `AUTHORING.md` §8) show the agent succeeding half the time, the task is not close — it is structurally at risk.

## Fair versus unfair difficulty

Difficulty must come from the problem being genuinely hard — never from information the agent could not have had.

- **Encouraged:** traps for plausible-but-wrong approaches (minimum two per task); precise behavioural contracts; forced investigation of the environment; hostile-but-stated edge cases.
- **Automatic rejection:** any hidden test checking a requirement the instruction never stated.
- **The human test:** an experienced engineer reading only the instruction and exploring the environment must be able to produce a fully correct solution. We verify this with an independent human solver before calibration.

## Who runs what

- **You** validate the oracle and self-check difficulty with local Harbor agent runs (`terminus-2` by default; `antigravity` or `gemini-cli` for a Gemini-flavoured pass).
- **Askable's calibration lead** runs the authoritative 10-attempt calibration against `calibration-target.json`. You do not need model API access for acceptance.
