# T28 Docs Finalization + Issue Triage — Implementation Plan

> Implementer input (Sonnet). Steps use `- [ ]` checkboxes. Planned 2026-09-13 against `a258384`.

**Goal:** Docs match merged tree (fresh clone → sample experiment reproducible from READMEs alone); zero doc refs to dead paths; folded GH issues get *drafted* closure refs (closed later at base→main merge, NOT by agent); meeting-notes ideas triaged into ROADMAP §5 (NOT GH issues); 4 carried hygiene leftovers fixed.

**Context:** Last P4 ticket. ROADMAP T28 stale-check (2026-08-25) + P3 verdict + T27 leftovers re-verified live on `a258384` during planning (2026-09-13). Plan written against merged tree — paths below verified, but re-grep before editing (ROADMAP §2 rule).

## User decisions (binding — override ROADMAP T28 text)

1. **GH issues: DO NOT close, comment, or create any issue.** No `gh issue close/comment/create`. Only draft closure refs into ROADMAP §7 (closed manually at base→main merge).
2. **Meeting-notes ideas → ROADMAP §5 findings, NOT GH issues.**
3. **`documentation/docs/meeting-notes.md` is immutable history — do NOT edit/trim it.** Rest of `documentation/` also untouched (ROADMAP §6 default).
4. **In scope extras:** untrack `experiments/.coverage`; drop dead `notebook` dep + relock; add `INSTANCE_SIZE`+`TOTAL_COST` to sample analysis config; `[project.urls]` repository → `algorithmic-econ`.

## Global constraints

- Branch `feat/t28-docs-triage` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch`. Never main.
- Refactor/docs-only. No src logic changes. No golden regen (nothing here touches runner/analyzer/fixtures).
- ROADMAP §6 already says root `CLAUDE.md` documents 4 subprojects → no CLAUDE.md edit.
- ruff: use solvers venv ruff 0.15.1 (global ruff 0.14 mismatch — leftovers T06/T25).
- Machine: bindings source builds need `export SDKROOT=$(xcrun --show-sdk-path); export CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"` (broken CLT). System `python3` = 3.14 → use `/opt/homebrew/bin/python3.13`.
- Sample scripts call bare `python` → need venv on PATH (see Task 5 for documented invocation; verify it works).
- Docs prose style: concise, match existing READMEs. No emojis added.

## Verified live facts (2026-09-13)

- Open GH issues: #20 #22 #23 #24 #25 #26 #27 #30 #31 #32 #34 #35 #36. Folded = #20 #22 #23 #24 #25 #26 #27 #32 #36. Excluded (§5) = #30 #31 #34 #35.
- Ticket commits on base: T06 `3fe7618` (#42), T07 `ae5a2a9` (#43), T08 `3cd0db9` (#44), T10 `e7408e4` (#46), T11 `69047d2` (#47), T13 `12c6c8f` (#49), T14 `b461f27` (#53), T15 `a7b6be0` (#50). Re-confirm with `git log --oneline`.
- Dead doc refs found:
  - `solvers/README.md:19` → standalone `jasieksz/muoblpbindings` repo.
  - `solvers/README.md` "Example Solver" → `src/muoblpsolvers/summed/SummedObjectivesLpSolver.py` (real: `src/muoblpsolvers/summed_objectives_lp_solver.py`).
  - `experiments/sample-experiment/README.md`: `:55` `solver_options: ["use-gurobi"]` (now dict of ctor kwargs, key `use_gurobi`); `:57` stray `x` line; `:62-70` `ConstraintConfig(TypedDict)` snippet (now Pydantic `StrictModel`, `helpers/runners/model.py:43`); `:76` link `../resources/input/constraint-config/sample-constraints.jsonc` (deleted T09); `:103-111` filename shape missing `utility_type` + links into `results/partial–sample-experiment/` (never existed; results gitignored); §5 analyzer config omits `concurrency` field (`AnalyzerConfig.concurrency: int = 3`).
  - `core/pyproject.toml:19`, `solvers/pyproject.toml:22` repository → `jasieksz/multiobjective-lp` (repo is `algorithmic-econ/multiobjective-lp`). **Keep `documentation` URL `https://jasieksz.github.io/multiobjective-lp`** — live (200); algorithmic-econ pages 404.
  - Root `README.md:40` ruff.yml statement OK; root README lacks test.yml / dev workflow / publish order.
  - `bindings/README.md` "broken CommandLineTools workaround … on this machine" — machine-specific wording.
- `core/example/define_pb.py` exists (T27), `core/README.md` link valid.
- `git ls-files '*.DS_Store'` empty; `experiments/.coverage` tracked; `.gitignore` has no coverage rule.
- `experiments/pyproject.toml:40` `notebook = "^7.5.4"` — zero refs (T25).
- Sample config `experiments/sample-experiment/sample-analysis-config.jsonc` metrics = `EXCLUSION_RATION, SUM_OBJECTIVES, EJR_PLUS`. `Metric` enum: + `CONSTRAINTS, INSTANCE_SIZE, TOTAL_COST`. `EXCLUSION_RATION` typo is load-bearing — do NOT fix.
- Entrypoints (`experiments/src/`, all `sys.argv[1]` = config path): `experiment_runner.py` (ExperimentConfig or CompactExperimentConfig), `analyzer_runner.py` (AnalyzerConfig; exit 1 on any failed analysis), `aggregate_results.py` (AggregatorConfig, `helpers/analyzers/model.py:55`), `generate_sweep_config.py` (SweepSpec, `helpers/runners/model.py`), `generate_experiment_config.py` (interactive `questionary`, needs TTY, no args).
- Solvers (10; pulp name / experiments `Solver` enum / bindings? / ctor options):
  - `Greedy` / GREEDY / no / —
  - `Phragmen` / PHRAGMEN / no / `increasing_scalings=False, kappa=1.0, bos_version=False, eps=1e-6`
  - `SummedObjectives` / SUMMING / no / `use_gurobi=False`
  - `MethodOfEqualSharesExponential` / MES_EXPONENTIAL / no / `budget_init` REQUIRED
  - `MethodOfEqualSharesConstrains` / MES_CONSTRAINT / yes / `cost_modification_base=1.007, max_iterations=200`
  - `MethodOfEqualSharesAdd1` / MES_ADD1 / yes / —
  - `MethodOfEqualSharesUtility` / MES_UTILS / yes / —
  - `SingleTransferableVote` / STV / yes / —
  - `ExpandingApprovals` / EXPANDING_APPROVALS / yes / —
  - `SolidCoalitionRefinement` / SOLID_COALITION_REFINEMENT / yes / —
  - Re-verify each against `__init__` signatures + `available()` before writing.
- Contracts to document (from leftovers T10–T16): options = ctor kwargs (serialized by `toDict()`); `available()` truthful (binding-backed → `bindings_available()`); `actualSolve` sets + returns `lp.status`; `msg=False` → silent; `timeLimit` honored by pure-python loops, MES-Constrains coarse per-iteration, other binding-backed `warnings.warn` + ignore (D8); PB solvers (all except SummedObjectives) run `validate_election_program` → `PulpSolverError`; known gap: MES-family/STV/EA/SCR ignore GE constraints (T31/D15).

## Meeting-notes triage (verified status — input for Task 7)

| Note idea (`meeting-notes.md` line) | Status |
|---|---|
| LB constraint strategies (`:12-23`) | DONE — `Strategy` enum `district_budget_minus_max`/`category_vote_share`/`category_cost_share` (`experiments/src/helpers/runners/model.py:7`, applied `pabutools_to_molp.py:448,491`) |
| 5 LB experiment variants (`:25-30`) | NOT DONE — future (already §5) |
| PropRank/Phragmen removal constraint-based (`:101-103`) | DONE — `FeasibilityChecker` drop-loop (`phragmen.py` ~`:378-387`, T16) |
| Exp-MES B_init auto (`:112-125`) | PARTIAL — `budget_init` manual required param; option 1/2 auto-derivation not done → future |
| MES generic utilities (`:72-76`, `:127-133`) | PARTIAL — `MES_UTILS` exists; generic `prepare_mes_parameters`, per-var proportionality coefs, constraint normalization fallback, weight-aware bindings (`# TODO: weight-aware via binding update` in `mes_add1.py:42`, `mes_utility.py:42`, `mes_constrains.py:121`) not done → future |
| Objective sum relative to greedy (`:33-34`) | DONE — `AggregatorConfig.normalize_baseline` (T23) |
| Auto-detect utility type (`:36`) | DONE — `RunnerConfig.utility_type: Utility \| None` auto-detect |
| Gurobi inside solver for feasibility (`:38`, `:46-49`) | DONE differently — CBC completion ILP in `FeasibilityChecker` (T16) |
| Voter citywide+district dedup (`:144`) | verify; likely future |
| Carried (not in notes): DISTRICT/UPPER `ConstraintConfig` name collision (`pabutools_to_molp.py:509`), pulp-4.0 migration debt (leftovers T05), stale MkDocs code-reference (`documentation/docs/code-reference/*.md` point at `multiobjective_lp.model…`/`examples.summing…`) | OPEN, no owner → record |

Implementer: re-verify each row (grep) before writing; mark unverifiable rows "unverified".

---

### Task 1: Branch

- [ ] `git checkout feat/roadmap-base-branch && git pull && git checkout -b feat/t28-docs-triage`. Stop if tree dirty.

### Task 2: Hygiene — untrack `.coverage`

**Files:** `.gitignore`, `experiments/.coverage` (index only)

- [ ] `git rm --cached experiments/.coverage`; add `.coverage` rule to root `.gitignore` (e.g. under python section: `.coverage` + `htmlcov/`? — only `.coverage`, keep minimal).
- [ ] Verify: `git ls-files | grep -E '\.coverage$'` empty; `cd experiments && poetry run pytest --cov -q` then `git status --porcelain` shows no `.coverage`.
- [ ] Commit `T28: untrack experiments/.coverage`.

### Task 3: Hygiene — drop `notebook` dep

**Files:** `experiments/pyproject.toml`, `experiments/poetry.lock`

- [ ] Re-confirm zero refs: `grep -rn "notebook\|jupyter\|ipykernel" experiments --include=*.py --include=*.toml --include=*.sh --include=*.jsonc | grep -v poetry.lock`.
- [ ] Remove `notebook = "^7.5.4"` line; `cd experiments && poetry lock` (poetry 2.2.1 keeps locked versions). Inspect `git diff --stat poetry.lock` + `git diff poetry.lock | grep '^[-+]version'`: expect ONLY removals of notebook + its exclusive transitives, zero version bumps. If bumps appear → revert lock, retry; if unavoidable, STOP + report.
- [ ] `poetry sync` (removes orphans) → `poetry check --lock` → `poetry run pytest` (incl e2e) + `poetry run pyright`.
- [ ] Commit `T28: drop dead notebook dep`.

### Task 4: Hygiene — sample analysis metrics + project.urls

**Files:** `experiments/sample-experiment/sample-analysis-config.jsonc`, `core/pyproject.toml`, `solvers/pyproject.toml` (+ locks if `poetry check` demands)

- [ ] Sample config metrics → `["EXCLUSION_RATION", "SUM_OBJECTIVES", "EJR_PLUS", "INSTANCE_SIZE", "TOTAL_COST"]`. Confirm no test/golden reads it: `grep -rn "sample-analysis-config" experiments/tests experiments/src` (expect none / non-golden).
- [ ] `repository = "https://github.com/algorithmic-econ/multiobjective-lp"` in core + solvers. Keep `documentation` URL. `poetry check` both; if lock content-hash complains, `poetry lock` and confirm diff = hash only (experiments `poetry check --lock` too, path-dep chain).
- [ ] Commit `T28: sample analysis metrics + repo urls`.

### Task 5: `experiments/sample-experiment/README.md` + `experiments/README.md`

- [ ] First, empirically determine working fresh invocation from `experiments/sample-experiment/`: try `poetry run ./run.sh` (poetry discovers parent pyproject; cwd preserved). Fallback: `PATH="$(poetry -C .. env info --path)/bin:$PATH" ./run.sh`. Document whichever works; do NOT edit run.sh/analyze.sh unless neither works (then STOP + ask).
- [ ] Sample README fixes (all dead refs listed above):
  - §1.2: `solver_options` = optional dict of solver ctor kwargs, e.g. `{"use_gurobi": true}` for SUMMING, `{"kappa": 0.0}` for PHRAGMEN; delete stray `x`; list all 10 `solver_type` values; add `deduplicate_objectives` (bool, default false) + `results_base_path` (optional override).
  - Mention compact config form (`compact_config: true` + `runner_configs_generator`) in one short para, pointing to `helpers/runners/model.py`.
  - §1.3: replace TypedDict snippet with the Pydantic model fields (key/value/bound/budget_ratio/strategy, strategy values); drop dead `sample-constraints.jsonc` link, keep inline JSON example.
  - §3/§6: invocation from previous step + prerequisite `cd experiments && poetry install` (builds bindings, C++20 toolchain → link `../../bindings/README.md`).
  - §4: filename shape `{file_type}_{problem_id}_{data_source}_{utility_type}_{solver_type}.{ext}` (source: `helpers/utils/result_naming.py`); replace dead links with plain code-block example names, e.g. `meta_08-30T18-45-11_6305_krakow_2024_COST_MES_ADD1.json`; note cache: rerun skips already-solved (delete `results/` to force re-solve).
  - §5: add `concurrency` (default 3); metrics list = all 6 `Metric` values; example matches updated config.
  - New §7 Aggregate (short): `AggregatorConfig` fields + inline JSON example (`group_by: "city"` and `"instance_size_bucket"` w/ `normalize_baseline`), invocation `python ../src/aggregate_results.py <config>` using same venv method. No new committed config file.
  - Input §2: pabulib links in `input/*/link.txt`.
- [ ] `experiments/README.md`: setup (py3.13, poetry, `poetry install` builds core/solvers/bindings path deps); entrypoints table (5 scripts above, arg, config model); tests (`poetry run pytest`, `-m e2e`, golden regen `UPDATE_GOLDEN=1` — fails by design, separate justified commit, normalization in `tests/golden_utils.py`); pyright; note `archived_code/` = excluded dead code; `preflib_to_muoblp.py` staged not dead (T25 directive); link sample README + `tests/fixtures/README.md`.
- [ ] Commit `T28: experiments docs sync`.

### Task 6: `solvers/README.md`, `core/README.md`, `bindings/README.md`

- [ ] solvers:
  - Replace `:19` dead link → "C++ bindings live in monorepo [`bindings/`](../bindings/README.md)".
  - Fix Example Solver path → `src/muoblpsolvers/summed_objectives_lp_solver.py`; "extends `LpSolver`, overrides `actualSolve(lp)`, sets + returns `lp.status`".
  - Add "Solvers" table (10 rows from facts above: pulp name, class, bindings-backed, options).
  - Add "Solver contract" section: ctor kwargs/options (`toDict()` serialization; `None` kwargs dropped by pulp), `available()`, status, `msg`, `timeLimit` (D8 behavior), PB validation → `PulpSolverError`, known GE-constraint limitation (T31/D15 pending).
  - Add "Development": `cd solvers && poetry install` (builds `../bindings` from source → toolchain, link bindings README) + `poetry run pytest` / `pyright` / `ruff`.
  - Keep existing PuLP registration section.
- [ ] core: add "Development" (`poetry install`, `pytest`, `pyright`); keep example + limitations. Verify `poetry run python example/define_pb.py` runs.
- [ ] bindings: generalize "on this machine" → "on macOS with broken CommandLineTools"; otherwise leave (stale-check: adequate). Verify `.pyi`/functions list still matches `src/muoblpbindings/__init__.pyi`.
- [ ] Commit `T28: core/solvers/bindings docs`.

### Task 7: Root `README.md`

- [ ] Overview: bindings bullet — "consumed by `solvers` (path dep in dev, version range when published)".
- [ ] New "Development workflow": prerequisites (Python 3.13, Poetry 2.x, C++20 toolchain + CMake auto via scikit-build-core, pre-commit); per-project venv (`cd <proj> && poetry install && poetry run pytest`); dependency chain core ← solvers ← experiments, bindings ← solvers; ruff 0.15.1 via solvers dev group (`cd solvers && poetry run ruff check .. && poetry run ruff format --diff ..` — verify exact cmd matches ruff.yml); pyright per project; e2e golden; sample-experiment entry point link.
- [ ] "GitHub Workflows": add test.yml (build-bindings wheel → test matrix core/solvers/experiments vs built wheel for solvers → pyright matrix; runs on PRs + pushes to main/base); keep ruff.yml; publish section: add publish order bindings → core → solvers, tag must equal pyproject version (validate-tag), `skip-existing`, rc → TestPyPI.
- [ ] Keep MkDocs section + jasieksz.github.io link as-is.
- [ ] Commit `T28: root README dev workflow`.

### Task 8: ROADMAP §5 findings + §7 closure drafts

**Files:** `ROADMAP.md`

- [ ] §5: append subsection `### Meeting-notes triage (T28, 2026-09-xx)` — table from "Meeting-notes triage" above (re-verified), note "notes file kept immutable (user decision); ideas NOT filed as GH issues (user decision)". Append `### Unowned findings (T28)`: DISTRICT/UPPER name collision, pulp-4.0 migration debt, stale MkDocs code-reference, P3 verdict #5 district city label `Poland_krakow_2024`, `os.path` residue `pabutools_utils.py:49-57` (T30 candidate), interactive generator TTY never click-tested.
- [ ] §7: add column "Close refs (draft — close at base→main merge)" per folded issue: PR # + short SHA. Mark #25 "keep open → T29 (publish never exercised)" and #36 "keep open → T31/D15 (GE gap)". Add ready-to-paste block for base→main PR body: `Closes #20, Closes #22, Closes #23, Closes #24, Closes #26, Closes #27, Closes #32` (GitHub auto-closes on merge to default branch). Replace "closed with commit refs in T28" sentence accordingly.
- [ ] T28 ticket: `[x]`, PR link, short "From T28 session" note (decisions 1–4).
- [ ] Commit `T28: ROADMAP triage findings + closure drafts`.

### Task 9: Dead-ref sweep + fresh-clone verify

- [ ] Grep (expect empty outside `plans/`, `ROADMAP.md`, `documentation/`, `papers/`, `archived_code/`):
  `git grep -nE "jasieksz/muoblpbindings|mes-standard-experiments|resources/input|partial–sample|use-gurobi|TypedDict|summed/Summed|problemRunner|experimentRunner|analyzerRunner" -- '*.md' '*.toml' '*.sh' '*.jsonc'`
  and `git grep -n "github.com/jasieksz" -- '*.md' '*.toml'` (only allowed: none; github.io docs URL OK).
- [ ] Link check: for every relative link in the 6 edited READMEs, confirm target exists (small scratch script in scratchpad, not committed).
- [ ] Fresh-clone reproduce (AC): `git clone <local repo path> $SCRATCH/t28-clone && cd $SCRATCH/t28-clone && git checkout feat/t28-docs-triage`; follow ONLY README instructions with `/opt/homebrew/bin/python3.13` (`poetry env use`), CLT env vars; run sample `run.sh` + `analyze.sh` per documented invocation. Expect metrics match frozen refs: APPROVAL 0.0033/219239/167; COST 0.0035/1.34763e11/0; COST_ORDINAL 0.0032/2.79444e11/0; bronowice 0.0666/4.35159e9/0; plus INSTANCE_SIZE/TOTAL_COST now present. Run documented aggregator bucket-mode example → PNG produced. Any README step that fails → fix README, repeat. Delete clone after (and `poetry env remove` its venvs).
- [ ] Full green: core/solvers/experiments `poetry run pytest` + `pyright`; `cd experiments && poetry run pytest -m e2e` (no regen, `git status experiments/tests` clean); ruff check + format repo-wide (solvers venv).

### Task 10: Leftovers + PR

- [ ] Append `### From T28 (PR feat/t28-docs-triage, <date>)` to `plans/leftovers.md`: user decisions 1–4, invocation method that worked, notebook lock diff summary, any README step that failed in fresh clone, remaining unowned findings, reminder: issues to close at main merge + solvers PyPI install broken until T29 (bindings 0.0.18 unpublished).
- [ ] Commit, push, `gh pr create --base feat/roadmap-base-branch --head feat/t28-docs-triage`, title `T28: docs finalization + issue triage`, body: what / AC / verify / closure-draft block pointer. End body with Claude Code attribution. STOP.

## AC

- Fresh clone + READMEs only → sample run+analyze reproduce frozen metrics.
- No doc refs to dead paths (Task 9 greps empty; relative links resolve). MkDocs `documentation/` excluded (recorded in §5).
- ROADMAP §5 triage + §7 closure drafts present; no GH issue mutated.
- `.coverage` untracked+ignored; `notebook` gone, lock no bumps; sample config has INSTANCE_SIZE/TOTAL_COST; urls → algorithmic-econ.
- All pytest/pyright/ruff/e2e green, no golden regen.

## Unresolved questions

1. Stale MkDocs code-reference (`documentation/docs/code-reference/*.md`): plan leaves untouched (§6) + records in §5. Fix instead?
2. Solvers README: mention `pip install muoblpsolvers` currently unresolvable until T29 publishes bindings 0.0.18? Plan: no README note, leftovers only.
3. If `poetry run ./run.sh` fails and PATH hack is ugly: OK to change run.sh/analyze.sh to `poetry run python …`? Plan: STOP + ask.
4. Aggregator: inline README example only (plan) vs committed `sample-aggregator-config.jsonc` + `aggregate.sh`?

## Steps

1. Branch `feat/t28-docs-triage`.
2. Untrack `experiments/.coverage` + gitignore.
3. Drop `notebook`, relock, verify no bumps.
4. Sample analysis metrics + repo urls.
5. Experiments + sample-experiment READMEs.
6. Solvers/core/bindings READMEs.
7. Root README dev workflow + CI/publish.
8. ROADMAP §5 triage, §7 closure drafts, T28 `[x]`.
9. Dead-ref grep, link check, fresh-clone reproduce, full green.
10. Leftovers, PR, stop.
