# Archived GitHub Actions workflows

These workflows are preserved for provenance but intentionally kept outside `.github/workflows/`, so they do not appear as active Actions.

The Stage 1 primary analysis was frozen on 2026-10-05. One-off rescue, recovery, parameter-study, pre-freeze final-run, Stage 2/3 extension, and obsolete packaging workflows were archived here after the freeze.

Active workflows are intentionally limited to:

- `ci.yml` — syntax, data, and smoke checks
- `run-test-k50.yml` — small reproducibility test
- `run-stage1-batch.yml` — generic Stage 1 validation/batch runner

Do not move an archived workflow back into `.github/workflows/` unless a new analysis version is explicitly started.
