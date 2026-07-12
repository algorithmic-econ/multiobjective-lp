# T04 — Unify Python → 3.13

## Context
Roadmap P1. Most of T04 already done in T03 (PR #39): experiments `requires-python >=3.13`, experiments+solvers locks regenerated on 3.13, test.yml CI matrix on 3.13, all local venvs recreated on 3.13. Remaining delta:

- `core/pyproject.toml:13` — `requires-python = ">=3.11"` → `">=3.13"`; core lock metadata still `>=3.11`.
- `.github/workflows/publish.yml:29` — build job `python-version: "3.12"` → `"3.13"`.
- Solvers/experiments locks record `muoblp` dep with old python constraint → refresh after core bump.

Core deps trivial (pulp 2.9.0 + dev pytest/pyright) — no real 3.13 fallout expected. Transitive bumps from relock accepted silently (T03 precedent).

## Changes
1. `core/pyproject.toml`: `requires-python = ">=3.13"`.
2. `cd core && poetry lock && poetry install` (recreate/refresh venv 3.13 — already on 3.13 per leftovers).
3. `cd solvers && poetry lock && poetry install`; same in `experiments` (refresh recorded muoblp constraint; expect small/no diff — locks already `>=3.13`).
4. `.github/workflows/publish.yml`: setup-python `3.12` → `3.13`.
5. Do NOT touch: publish.yml `poetry install`-before-build / 400 diagnosis (T08), pulp pin (T05), bindings (T06).

## Verify
- `cd core && poetry run pytest` (smoke test from T03); same solvers, experiments.
- `cd experiments && poetry run pytest -m e2e` — golden unchanged, no regen.
- ruff + pyright per project.
- Push branch `feat/t04-python-313`, PR → `feat/roadmap-base-branch`; Actions green (test.yml only; publish.yml is tag-triggered — cannot verify CI-side without tag, tag-based dry run is T08 territory).
- Append findings to `plans/leftovers.md`.

## Unresolved questions
- None blocking. Publish.yml change is unverifiable in CI until a tag push (T08 does rc-tag dry run) — accepting review-only verification here.

## Steps
1. Branch `feat/t04-python-313` off `feat/roadmap-base-branch`.
2. Bump core `requires-python` → `>=3.13`; `poetry lock && poetry install` in core.
3. `poetry lock && poetry install` in solvers + experiments; inspect diffs.
4. publish.yml python 3.12 → 3.13.
5. Run pytest in all 3 projects + e2e golden + ruff/pyright.
6. Update ROADMAP checkbox, append leftovers, commit, PR → `feat/roadmap-base-branch`, confirm Actions green.
