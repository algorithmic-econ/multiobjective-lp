# T21 snake_case Renames + Entrypoint/Doc Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `git mv` every remaining camelCase module in `experiments/src` to snake_case, fix the "Phargmen" misspelling, make imports consistently absolute; sync run.sh/analyze.sh, sample-experiment README, and test imports in the SAME ticket. Zero behavior change.

**Architecture:** Pure rename ticket. Module filenames do NOT leak into result filenames (those come from `pipeline/paths.py` post-T20) → e2e golden untouched by construction. Renames + import updates land atomically per commit (repo green after each). Aggregators get renamed ONLY — their broken `from src.helpers` imports stay broken until T23 (roadmap assigns the fix there). No content edits beyond import lines + one stale comment.

**Tech Stack:** `git mv`, ruff/pyright/pytest as rename verification; existing e2e golden harness.

## Global Constraints

- Branch `feat/t21-snake-case` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`.
- **Execute AFTER T19+T20 merge; verify tree first.** Assumed post-state: `resultCache.py` → `pipeline/cache.py` and `expand_experiment_config.py` → `pipeline/config.py` (T20 — both OFF the roadmap's T21 list now), `molpToSimpleElection.py` archived (T16), `pabutoolsToMoLp.py` imports `AgentId`/`District` from `.pabutoolsUtils` (T19 Task 5). If tree differs, re-derive the rename/import lists by grep before editing.
- e2e golden IDENTICAL, NO regen. No logic edits — import statements, script command lines, doc links, one stale comment only.
- All commands from `experiments/`, its poetry venv. Pre-commit hooks (ruff, ruff-format) may rewrap long import lines — fine.
- Repo GREEN after ticket: experiments pytest (units+e2e) + ruff + pyright (0 errors, post-T19 config); core/solvers/bindings untouched — one confirming pytest each at end.

## Rename map

| old (post-T20 tree) | new |
|---|---|
| `src/experimentRunner.py` | `src/experiment_runner.py` |
| `src/problemRunner.py` | `src/problem_runner.py` |
| `src/analyzerRunner.py` | `src/analyzer_runner.py` |
| `src/generateExperimentConfig.py` | `src/generate_experiment_config.py` |
| `src/generateCompactExperimentConfig.py` | `src/generate_compact_experiment_config.py` |
| `src/generateExperiment.py` | `src/generate_experiment.py` |
| `src/generatePhargmenGreedyDistrictExperiment.py` | `src/generate_phragmen_greedy_district_experiment.py` |
| `src/aggregateResults.py` | `src/aggregate_results.py` |
| `src/aggregateGroupedResults.py` | `src/aggregate_grouped_results.py` |
| `src/helpers/runners/solverStrategy.py` | `src/helpers/runners/solver_strategy.py` |
| `src/helpers/runners/sourceStrategy.py` | `src/helpers/runners/source_strategy.py` |
| `src/helpers/utils/enhanceFromSolverResult.py` | `src/helpers/utils/enhance_from_solver_result.py` |
| `src/helpers/transformers/pabutoolsToMoLp.py` | `src/helpers/transformers/pabutools_to_molp.py` |
| `src/helpers/transformers/pabutoolsUtils.py` | `src/helpers/transformers/pabutools_utils.py` |
| `src/helpers/transformers/pabutoolsConstants.py` | `src/helpers/transformers/pabutools_constants.py` |
| `src/helpers/transformers/preflibToMuoblp.py` | `src/helpers/transformers/preflib_to_muoblp.py` |

(`preflibToMuoblp` is NOT in the roadmap's T21 list but AC "no camelCase filenames" requires it; T25 archives it right after — rename is 1 line of churn, keeps AC grep clean. Note in PR.)

---

### Task 1: Rename helpers modules + import sync

**Files:**
- Move: 6 helpers files (map above, `helpers/` rows) via `git mv`
- Modify (import lines only): `src/pipeline/cache.py`, `src/pipeline/problem_steps.py`, `src/pipeline/analyzer_steps.py`, `src/problemRunner.py`, `src/helpers/runners/source_strategy.py`, `src/helpers/transformers/pabutools_to_molp.py`, `tests/test_solver_strategy.py`, `tests/test_ballot_strategies.py`, `tests/test_constraint_computation.py`, `tests/test_constraint_creation.py`, `tests/test_pabutools_to_molp.py`

- [ ] **Step 1: git mv ×6** (solverStrategy, sourceStrategy, enhanceFromSolverResult, pabutoolsToMoLp, pabutoolsUtils, pabutoolsConstants → snake_case per map).

- [ ] **Step 2: Update import statements.** Old→new module paths:
  - `helpers.runners.solverStrategy` → `helpers.runners.solver_strategy` (problemRunner, test_solver_strategy)
  - `helpers.runners.sourceStrategy` → `helpers.runners.source_strategy` (pipeline/cache, pipeline/problem_steps)
  - `helpers.utils.enhanceFromSolverResult` → `helpers.utils.enhance_from_solver_result` (pipeline/analyzer_steps)
  - `helpers.transformers.pabutoolsToMoLp` → `helpers.transformers.pabutools_to_molp` (source_strategy + 4 test files)
  - `helpers.transformers.pabutoolsUtils` → `helpers.transformers.pabutools_utils` (source_strategy)
  - `helpers.transformers.pabutoolsConstants` → `helpers.transformers.pabutools_constants` (test_constraint_creation)
  - Inside `pabutools_to_molp.py`: relative `.pabutoolsConstants` / `.pabutoolsUtils` → absolute `helpers.transformers.pabutools_constants` / `...pabutools_utils` (ticket AC: consistent absolute imports).

- [ ] **Step 3: Run** — `cd experiments && poetry run pytest -q` (incl. e2e) green; `grep -rn "solverStrategy\|sourceStrategy\|enhanceFromSolverResult\|pabutoolsToMoLp\|pabutoolsUtils\|pabutoolsConstants" src tests` → empty.

- [ ] **Step 4: Commit** — `git commit -am "T21: snake_case helpers modules"`

---

### Task 2: Rename entrypoints + generators + aggregators, sync scripts + tests

**Files:**
- Move: 9 `src/` root files (map above) via `git mv`
- Modify: `src/experiment_runner.py` (`from problemRunner import` → `from problem_runner import`), `src/generate_compact_experiment_config.py` (`from generateExperimentConfig import` → `from generate_experiment_config import`), `tests/test_e2e_golden.py` (`import analyzerRunner` / `import experimentRunner` → snake_case + call sites; also fix stale "trailing slashes required" comment — T20 removed the f-string concat), `sample-experiment/run.sh`, `sample-experiment/analyze.sh`

- [ ] **Step 1: git mv ×9** per map (incl. Phargmen→phragmen fix).

- [ ] **Step 2: Update the 5 files above.** Aggregators: filename rename ONLY, do NOT fix their `from src.helpers` imports (T23 rewrites both; they are standalone scripts, nothing imports them — pytest/ruff/pyright status unchanged).

- [ ] **Step 3: Run** — full `poetry run pytest -q && poetry run pytest -m e2e -q` green (e2e imports the renamed entrypoints).

- [ ] **Step 4: Sample smoke** — `cd sample-experiment && rm -rf results/* && PATH="$(poetry -C .. env info --path)/bin:$PATH" ./run.sh && ./analyze.sh` (same PATH) → metrics match reference values (T01/T05 refs).

- [ ] **Step 5: Commit** — `git commit -am "T21: snake_case entrypoints/generators/aggregators; sync scripts"`

---

### Task 3: Doc sync + config no-op checks

**Files:**
- Modify: `sample-experiment/README.md` (links `solverStrategy.py`→`solver_strategy.py`, `sourceStrategy.py`→`source_strategy.py`; grep for other module mentions)

- [ ] **Step 1: Fix README links**; `grep -rn "[a-z]\+[A-Z][a-zA-Z]*\.py" experiments/*.md experiments/sample-experiment/*.md` → empty.

- [ ] **Step 2: No-op verifications** (record in PR): `pyrightconfig.json` has no module refs (extraPaths/exclude only) — nothing to update; `.github/workflows/*.yml` reference no experiments module paths (cache keys hash locks only); experiments/root READMEs have no camelCase module refs.

- [ ] **Step 3: Commit** — `git commit -am "T21: doc sync"`

---

### Task 4: Full verify + AC greps + PR

- [ ] **Step 1: Matrix** — `cd experiments && poetry run pytest -q && poetry run pytest -m e2e -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright` all green. Siblings: `cd ../solvers && poetry run pytest -q`; `cd ../core && poetry run pytest -q` (untouched).

- [ ] **Step 2: AC greps** — `find experiments/src -name "*[A-Z]*.py"` → empty; `grep -rn "Phargmen" . --include="*.py" --include="*.md" --include="*.sh"` → empty; roadmap grep `grep -rE "src/[a-z]+[A-Z]" experiments` → empty; `grep -rn "from \." experiments/src --include="*.py"` → empty (absolute imports everywhere).

- [ ] **Step 3: PR** — push, PR → `feat/roadmap-base-branch`, title `T21: snake_case renames + entrypoint/doc sync`. Body: rename table, preflib note, aggregator-imports-deferred-to-T23 note. Update ROADMAP checkbox + `plans/leftovers.md` (record final module names for T22–T26 plans; note `git mv` preserved history via rename detection).

## Unresolved questions

1. `preflibToMuoblp.py` renamed here then archived in T25 — OK, or archive early in T21 (saves churn, slightly widens ticket scope)?
2. Aggregators renamed with broken `src.helpers` imports left in place (T23's fix) — confirm no interim need to run them.

## Steps

1. Task 1: rename 6 helpers modules + import sync + commit
2. Task 2: rename 9 src-root files + script/test sync + sample smoke + commit
3. Task 3: README links + no-op checks + commit
4. Task 4: full verify, AC greps, PR, ROADMAP/leftovers update
