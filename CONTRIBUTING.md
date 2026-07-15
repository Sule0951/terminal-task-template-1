# Contributing a Terminal Task

This repository is source-available under the `LICENSE`; it is not an
open-source project. Before creating a task, sign the Askable participant
agreement and keep your fork private.

## Human-authorship policy

Task code must be written by a human contributor. You may use AI to brainstorm
task ideas or validate a finished task. You may not use AI to generate, translate,
rewrite, or modify:

- task implementation code
- Docker environments
- verifier code or tests
- oracle solutions
- task-specific scripts
- fixtures, datasets, or binaries

Every contributor must complete
`tasks/<task>/attestations/<github-handle>.md` against the task-code commit. The
attestation affirms human authorship, authority to contribute the material, and
assignment of all contribution rights to Askable.

## Third-party material and provenance

Create or update `tasks/<task>/provenance.json` for every third-party dependency,
code sample, dataset, binary, and fixture. Each item requires:

- name
- source URL or origin
- license
- version or content hash
- explanation of why its license or permission permits Askable's intended
  AI-training use

Use an empty `third_party_material` array only when no third-party material is
included. Do not include anything whose rights are uncertain.

## Submission process

1. Write the task and confirm the oracle solution earns reward `1`.
2. Set an approved category and non-empty primary-language list in `task.toml`.
3. Commit task code and provenance. Save that SHA as `TASK_CODE_COMMIT`.
4. Complete all contributor attestations using `TASK_CODE_COMMIT`.
5. Run the eight-attempt Opus 4.8 calibration and commit its results.
6. Run local checks:

   ```bash
   python3 -m unittest discover -s tests -v
   ./scripts/validate-submissions.sh
   ./scripts/validate-all.sh
   ```

7. Commit the calibration result and completed attestations in a second,
   immutable submission commit. Keep both commits and all required task files in
   your private repository.
