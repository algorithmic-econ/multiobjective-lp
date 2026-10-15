# T25 Dead Code Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move confirmed-dead experiments code to `archived_code/experiments/`: `preflib_to_muoblp.py`, `explore.ipynb`, `pabutools_utils.filter_projects`/`by_district`, `metrics.py` trailing commented drafts; grep-audit for anything else unreferenced.

**Architecture:** Deletion-shaped ticket, archive-not-delete per ROADMAP §2. Dead-status pre-verified (2026-07-19 tree): `preflibToMuoblp` — zero importers repo-wide; `explore.ipynb` — tracked, referenced nowhere; `filter_projects`/`by_district` — only definitions, zero call sites; `metrics.py:111-175` — commented `ejr_plus_violations`/`cost_sat_func` drafts. Re-verify each against the merged post-T24 tree before moving (T22 archived generators, T23 aggregators — lists may have shifted). Whole-module deaths = `git mv`; function/block deaths = cut into a companion archived file.

**Tech Stack:** git mv, grep import audit, ruff F401, pytest.

## Global Constraints

- Branch `feat/t25-dead-code` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- **Execute AFTER T21 merge (snake_case names assumed); phase order: after T22–T24** — their archivals (generate_compact/generate_experiment, aggregate legacy) are DONE, not this ticket's scope.
- e2e golden IDENTICAL, NO regen.
- Archive, never plain-delete (`archived_code/` excluded from ruff CI + pre-commit; pyright excludes it). Notebook: `explore.ipynb` moves as-is.
- Untracked disk leftovers (`experiments/.fleet/run.json` — stale camelCase+deleted-config refs; `experiments/resources/` runtime dir) are NOT git-tracked (verified) → do NOT touch; note in leftovers only.
- Repo GREEN after ticket: experiments pytest (units+e2e) + ruff + format + pyright; siblings untouched.

---

### Task 1: Archive whole-module dead code

**Files:**
- Move: `git mv experiments/src/helpers/transformers/preflib_to_muoblp.py archived_code/experiments/preflib_to_muoblp.py`
- Move: `git mv experiments/src/explore.ipynb archived_code/experiments/explore.ipynb`

- [ ] **Step 1: Re-confirm dead** — `grep -rn "preflib" experiments/src experiments/tests --include="*.py" | grep -v preflib_to_muoblp.py` → empty; notebook referenced nowhere (`grep -rn "explore.ipynb" . --exclude-dir=.venv --exclude-dir=archived_code`).
- [ ] **Step 2: git mv ×2.**
- [ ] **Step 3: Run** — `cd experiments && poetry run pytest -q` green; ruff clean.
- [ ] **Step 4: Commit** — `git commit -m "T25: archive preflib transformer + explore notebook"`

---

### Task 2: Cut dead functions/blocks

**Files:**
- Modify: `experiments/src/helpers/transformers/pabutools_utils.py` (delete `filter_projects`, `by_district`; `Callable`/`Project` imports may become unused — ruff will flag)
- Modify: `experiments/src/helpers/analyzers/metrics.py` (delete trailing commented block — pre-T24 lines 111-175: `ejr_plus_violations`, `cost_sat_func`, `get_project_sat`/`sat` drafts)
- Create: `archived_code/experiments/pabutools_utils_dead.py` (the 2 cut functions + header comment naming origin module + ticket)
- Create: `archived_code/experiments/metrics_commented_drafts.py` (the cut commented block verbatim + same header)

- [ ] **Step 1: Re-confirm dead** — `grep -rn "filter_projects\|by_district" experiments/src experiments/tests --include="*.py"` → only definitions (note: `load_pabutools_by_district` contains substring `by_district` — match on word boundary / exclude it).
- [ ] **Step 2: Cut + archive** as above; fix now-unused imports in `pabutools_utils.py`.
- [ ] **Step 3: Run** — pytest + ruff (`F401` clean) + pyright green.
- [ ] **Step 4: Commit** — `git commit -am "T25: archive dead pabutools_utils fns + metrics commented drafts"`

---

### Task 3: Unreferenced-module audit

- [ ] **Step 1: Build import graph** — for each module under `experiments/src` (recursive), grep its import path across `src`+`tests`+`sample-experiment/*.sh`; roots = entrypoints (`experiment_runner`, `problem_runner`, `analyzer_runner`, `aggregate_results`, `generate_experiment_config`, `generate_sweep_config`) + test files. Expected post-T22/T23/T24 tree: everything referenced; empty `__init__.py` files exempt.
- [ ] **Step 2: Archive any stragglers found** (same pattern as Tasks 1–2); if none, record audit table in PR body.
- [ ] **Step 3: Run** — full pytest.
- [ ] **Step 4: Commit** (only if stragglers) — `git commit -am "T25: archive unreferenced modules"`

---

### Task 4: Full verify + PR

- [ ] **Step 1: Matrix** — `cd experiments && poetry run pytest -q && poetry run pytest -m e2e -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright` green; `cd ../solvers && poetry run pytest -q`; `cd ../core && poetry run pytest -q`.
- [ ] **Step 2: AC greps** — `grep -rn "preflib\|filter_projects\|by_district\b" experiments/src --include="*.py"` → only `load_pabutools_by_district`; `poetry run ruff check --select F401 src` → clean; no `.ipynb` under `experiments/src`.
- [ ] **Step 3: PR** — push, PR → `feat/roadmap-base-branch`, title `T25: dead code sweep`. Body: archived inventory + audit table. Update ROADMAP + `plans/leftovers.md` (note untracked `.fleet/run.json` staleness for T28 docs triage; `pabutools_utils` now = `detect_utility_from_instances` + `load_pabutools_by_district` + aliases only).

## Unresolved questions

1. Untracked `experiments/.fleet/run.json` references deleted configs + old camelCase entrypoints — leave (untracked user IDE config, plan default) or delete from disk?
2. Commented block in `metrics.py` archived as file (plan) vs plain-deleted (git history keeps it; ROADMAP §2 says archive) — confirm archive.

## Steps

1. Task 1: archive preflib module + notebook + commit
2. Task 2: cut dead fns + commented drafts into archived files + commit
3. Task 3: unreferenced-module audit (+ archive stragglers) + commit if needed
4. Task 4: matrix, AC greps, PR, ROADMAP/leftovers update
