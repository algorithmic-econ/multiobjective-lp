# T03 — Baseline CI for all subprojects (+ experiments py3.13 pull-forward)

## Context

P0 safety net, last ticket before refactors. Today `.github/workflows/test.yml` runs pytest for **solvers only** (path-filtered). T03: CI = poetry install + pytest (incl. e2e golden) for core + solvers + experiments on every PR, plus pyright (basic) job per subproject. AC: green Actions run on branch; e2e golden runs in CI.

**Scope change (user-approved):** experiments python `>=3.11,<3.13` → `>=3.13` is pulled forward from T04 into T03. Reason: on py3.12 poetry resolves stale `muoblpbindings` 0.0.16 from PyPI (0.0.17 wheels are cp313-only), and `solvers/src/muoblpsolvers/__init__.py` eagerly imports `expanding_approvals`/`stv`/`scr` which 0.0.16 lacks → `import muoblpsolvers` crashes → e2e impossible in CI. On py3.13 poetry resolves 0.0.17 wheels (macos-arm64 + manylinux + musllinux exist) — no hack needed. Update ROADMAP: T04 loses the experiments-constraint bullet (keeps core `>=3.13`, CI/publish.yml python, residual fallout).

Branch: `feat/t03-baseline-ci` off `feat/roadmap-base-branch` (PRs #37, #38 merged there). PR targets `feat/roadmap-base-branch`.

## Current state (verified)

- `test.yml`: solvers-only; `on.push/pull_request` path-filtered to `solvers/**`; two latent bugs — cache key references unset step id `steps.setup-python` (empty interpolation) and cache `path: .venv` is repo-root while venvs are per-project (`virtualenvs-in-project: true` → `solvers/.venv`). Cache effectively broken.
- `ruff.yml` already lints all 3 projects (untouched). `publish.yml` untouched (T08).
- `core/`: `requires-python >=3.11`, dep `pulp==2.9.0` only, **no tests/ dir** → `pytest` exits 5 = CI fail. No dev group.
- `solvers/`: `>=3.13`; deps `muoblp` path-dep, `pulp 2.9.0`, `muoblpbindings==0.0.17`, pytest as **main** dep (fix = T18, not here). pytest config: `testpaths=["tests"]`.
- `experiments/`: `>=3.11,<3.13`; path deps on core+solvers; `package-mode=false`; pytest `pythonpath=["src"]`, marker `e2e`; dev group has pytest/pytest-cov. Lock currently pins bindings 0.0.16 (cp312) — regenerating on 3.13 must show 0.0.17 (this is also T04's old AC).
- pyright: nowhere except `experiments/pyrightconfig.json` = `{"extraPaths": ["src"]}`. No mode set, no CI job, not installed anywhere.
- Local: `/opt/homebrew/bin/python3.13` exists. Experiments venv is py3.12 with hand-built local bindings (leftovers T01) — recreate on 3.13.
- e2e golden: `cd experiments && poetry run pytest -m e2e`; plain `pytest` includes e2e (marker only labels). `UPDATE_GOLDEN=1` regen intentionally fails run. Goldens macOS-generated — **Linux tie-break divergence risk** (leftovers T02).

## Changes

### 1. Experiments → py3.13
- `experiments/pyproject.toml`: `requires-python = ">=3.13"`.
- `rm poetry.lock && poetry lock` (or `poetry lock --regenerate`); recreate venv: `poetry env use /opt/homebrew/bin/python3.13 && poetry install`.
- Verify `poetry show muoblpbindings` → 0.0.17. Fix any dep fallout (pabutools/pandas/notebook expected fine on 3.13); if a dep hard-blocks 3.13, stop and report (don't fork the design).
- Full local test: `poetry run pytest` (units + e2e) must be green on 3.13 **before** touching CI.

### 2. `core/tests/` smoke test
- `core/tests/test_import.py`: import `muoblp`, construct `MultiObjectiveLP` (see `core/src/muoblp/model/multi_objective_lp.py`), trivial assert. Prevents pytest exit-5 failing CI. Not a feature — test infra.

### 3. `test.yml` rewrite
- Triggers: `pull_request` (all branches, no path filter), `push` to `main` + `feat/roadmap-base-branch` only (avoids double runs on PR branches), `workflow_dispatch`.
- Job `test`, matrix: `project: [core, solvers, experiments]`, python `3.13` for all (post-bump).
- Steps per project: checkout → setup-python (give step `id: setup-python` — fixes key bug) → snok/install-poetry (in-project venvs) → cache `path: ${{ matrix.project }}/.venv`, key `venv-${{ runner.os }}-py<ver>-${{ matrix.project }}-${{ hashFiles('core/poetry.lock', 'solvers/poetry.lock', 'experiments/poetry.lock') }}` (path deps make locks interdependent; hashing all three is the safe key) → `poetry install --no-interaction` in `working-directory: ${{ matrix.project }}` → `poetry run pytest`.
- experiments job runs plain `pytest` = units + e2e golden. No special-casing.

### 4. pyright job
- Add `pyright` to dev dependency-group in each of the 3 pyprojects (core needs a new dev group; pin one recent version consistently, e.g. `^1.1`).
- Config per project — `pyrightconfig.json` with `"typeCheckingMode": "basic"`; experiments keeps `"extraPaths": ["src"]` and adds mode; exclude `archived_code`, `.venv`.
- CI job `pyright`, same 3-project matrix: poetry install → `poetry run pyright`.
- Green baseline: run locally per project first. Fix trivia; suppress the rest — prefer narrow inline `# pyright: ignore[rule]`; config-level `reportX` disables only if errors are bulk/systemic. Record every suppression in `plans/leftovers.md` for the D12 ratchet.

### 5. ROADMAP + leftovers bookkeeping
- Tick T03, add PR link; edit T04 bullet (experiments constraint done in T03; T04 AC about bindings ≥0.0.17 now satisfied — reword to core+CI python only).
- Append findings to `multiobjective-lp/plans/leftovers.md` (env changes: experiments venv now 3.13 w/ PyPI 0.0.17, local bindings hack obsolete; pyright suppression inventory; any Linux-CI observations for T07).

## Contingency — Linux golden mismatch (user-approved path)

If e2e fails on ubuntu CI with golden diff: diagnose the diff first. Pure ordering/formatting → extend normalization in `experiments/tests/golden_utils.py` (D11 scope, note in PR). Real value divergence (MES tie-breaks) → switch experiments matrix entry to `macos-15` runner, file GH issue documenting divergence. **No golden regeneration** (ticket doesn't allow).

## Verification

1. Local, per project: `cd <proj> && poetry install && poetry run pytest` green ×3 projects (core = smoke test).
2. Local e2e: `cd experiments && poetry run pytest -m e2e` green on py3.13 venv.
3. Local pyright: `poetry run pyright` green ×3.
4. Push branch, open PR → `feat/roadmap-base-branch`; watch Actions: 3 test jobs + 3 pyright jobs + ruff all green; confirm e2e ran in experiments job log; confirm cache populated on 2nd run (re-push or re-run).
5. macOS CommandLineTools breakage (leftovers) irrelevant here — bindings come as wheels, no local C++ build.

## Unresolved questions

1. pyright version pin — plan says one shared recent `^1.1` pin; OK, or want exact pin (e.g. match a specific version)?
2. experiments `notebook`/`seaborn` etc. on py3.13: if lock regen forces minor version bumps of transitive deps, accept silently or list them in PR description? (Plan default: list in PR.)
3. Push-trigger scope trimmed to `main` + `feat/roadmap-base-branch` (was: all branches) — confirm OK.

## Steps

1. Branch `feat/t03-baseline-ci` off up-to-date `feat/roadmap-base-branch`.
2. Experiments: `requires-python >=3.13`, regen lock, recreate venv on python3.13, `poetry install`, verify bindings 0.0.17, full pytest green locally.
3. Add `core/tests/test_import.py` smoke test; `cd core && poetry install && poetry run pytest` green.
4. Add pyright to dev groups (core/solvers/experiments), add/extend `pyrightconfig.json` ×3 (basic mode), run locally, fix/suppress to green; log suppressions.
5. Rewrite `.github/workflows/test.yml`: 3-project matrix, py3.13, fixed cache (per-project path, all-locks hash key), no path filters, push limited to main+roadmap-base, workflow_dispatch kept.
6. Commit, push, open PR → `feat/roadmap-base-branch`; watch Actions.
7. If Linux golden mismatch → contingency section (diagnose; normalization fix or macos-15 runner + issue).
8. On green: tick T03 in ROADMAP + PR link, shrink T04 scope note, append leftovers.md findings; verify pre-commit hooks passed.
