# P3 Verify — Phase 3 Experiments-Refactor Judge Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans, single session — verification is sequential, findings must accumulate in one context (subagent-per-task NOT recommended). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently verify Phase 3 (T19–T26) complete + green on `feat/roadmap-base-branch`; re-check every ticket AC verbatim; adjudicate leftovers + each T-plan's unresolved questions; record `P3 judge verdict` in `plans/leftovers.md` with GO/NO-GO for P4 (T27/T28). T26-plan explicitly anticipates this session.

**Architecture:** Judge session per P1/P2 precedent: independent green matrix + AC re-verification + verdict, bookkeeping-only commit to base. Every check = command + expected output. Failing check → **BLOCKING** (AC broken → NO-GO, fix ticket) or **NON-BLOCKING** (leftovers note). Nothing fixed in-session. Heavy path-dependence on T19–T26 outcomes (renames, enum spellings, fixture paths) — re-derive exact names vs merged tree before each path-sensitive check; judge substance not spelling.

**Tech Stack:** experiments poetry venv (existing — no fresh-venv here, user-confirmed; P2 covered install-path), pytest, ruff, pyright, `gh` CLI, scratch configs in session scratchpad.

## Global Constraints

- Run ON `feat/roadmap-base-branch` directly, AFTER T19–T26 merged (P2 verdict must be GO).
- **Verification-only (user-confirmed):** NO src edits, NO golden regen (post-T19 goldens = final; `instance_size` 10). Only allowed edits: ROADMAP bookkeeping + leftovers verdict; single `docs: P3 judge verdict — ...` commit.
- Scratch configs/scripts under session scratchpad, never committed; corrupt-meta smoke mutates only gitignored `sample-experiment/results/*`.
- Test counts recorded, not asserted. Frozen sample metrics refs (T01/T05) ARE asserted.
- All experiments commands from `experiments/`, its venv; sample scripts need venv python on PATH.
- Assumed post-T21 names: `experiment_runner.py`, `problem_runner.py`, `analyzer_runner.py`, `aggregate_results.py`, `generate_experiment_config.py`, `generate_sweep_config.py`, `pipeline/{paths,config,cache,problem_steps,analyzer_steps}.py`.

---

### Task 1: Preflight — branch, merges, bookkeeping

- [ ] **Step 1:** `git checkout feat/roadmap-base-branch && git pull` → clean, up to date.
- [ ] **Step 2:** `git log --oneline -20` → T19–T26 merges present; ROADMAP T19–T26 all `[x]` + PR links (stale → reconcile in Task 10).
- [ ] **Step 3:** Re-read leftovers T19 onward; collect each T19–T26 plan's "Unresolved questions" → audit list for Task 10 (was each answered/landed/moot? e.g. T19 Solver enum spellings, T20 lib name `pipeline`, T22 sweep rename, T23 aggregator name, T24 mixed failure rows, T25 .fleet/run.json).

### Task 2: Full green matrix + determinism + pyright ratchet accounting

- [ ] **Step 1:** `cd experiments && poetry install && poetry run pytest -q && poetry run ruff check . && poetry run ruff format --check . && poetry run pyright` → all pass, pyright 0. Record count (~54 transform + T19–T26 additions).
- [ ] **Step 2:** Determinism (T02 AC bar): `poetry run pytest -m e2e -q` ×3 consecutive → identical pass, NO regen.
- [ ] **Step 3:** Siblings untouched-by-P3 confirm: `cd ../core && poetry run pytest -q`; `cd ../solvers && poetry run pytest -q` → green.
- [ ] **Step 4:** Ratchet accounting (D12): read `experiments/pyrightconfig.json` → list rules still disabled; compare vs T03 baseline (10 rules / 76 errors). Expected: most gone (T19/T23 ratchet tasks); record before/after per rule for verdict. `grep -rn "pyright: ignore" experiments/src | wc -l` → record.

### Task 3: Schema boundaries (T19)

- [ ] **Step 1:** Broken-config feed:

```bash
cat > <scratchpad>/broken-config.json <<'EOF'
{"concurrency": 1, "experiment_results_base_path": "results/",
 "runner_configs": [{"solver_type": "MES", "source_type": "PABUTOOLS",
                     "source_directory_path": "input/krakow_2024"}]}
EOF
cd experiments/sample-experiment
PATH="$(poetry -C .. env info --path)/bin:$PATH" \
  python ../src/experiment_runner.py <scratchpad>/broken-config.json; echo exit=$?
```

Expected: `ValidationError` naming `runner_configs.0.solver_type`, nonzero exit, zero solves started.
- [ ] **Step 2:** Greps — `grep -rn "TypedDict" experiments/src` → empty; `grep -rn "METADATA" experiments/src` → empty.
- [ ] **Step 3:** Sample-config conformance tests pass (already in matrix; spot): `cd experiments && poetry run pytest tests/test_models.py -q` → green.

### Task 4: Pipeline lib + rename ACs (T20/T21)

- [ ] **Step 1:** Thin entrypoints — `wc -l src/experiment_runner.py src/problem_runner.py src/analyzer_runner.py` → each ≤ ~55.
- [ ] **Step 2:** pathlib/concat greps — `grep -rn "os\.path\|os\.listdir" experiments/src --include="*.py"` → empty; `grep -rn "split('/'\|split(\"/" experiments/src --include="*.py"` → empty; `grep -rn "_path}{" experiments/src --include="*.py"` → empty.
- [ ] **Step 3:** Rename greps — `find experiments/src -name "*[A-Z]*.py"` → empty; `grep -rn "Phargmen" . --include="*.py" --include="*.md" --include="*.sh"` → empty; `grep -rn "from \." experiments/src --include="*.py"` → empty (absolute imports).
- [ ] **Step 4:** Filename dedup contract — `poetry run pytest tests/test_pipeline_paths.py tests/test_pipeline_cache.py -q` → green (writer↔regex roundtrip is THE dedup guard).

### Task 5: Generators (T22)

- [ ] **Step 1:** Automated generate→run test green (in matrix; spot): `poetry run pytest tests/test_generators.py -q`.
- [ ] **Step 2:** Manual sweep generate→run in scratchpad:

```bash
cat > <scratchpad>/sweep-spec.json <<'EOF'
{"mode": "citywide", "root_path": "tests/fixtures/input",
 "solvers": [{"type": "GREEDY"}], "concurrency": 1,
 "experiment_results_base_path": "<scratchpad>/sweep-results/",
 "output_path": "<scratchpad>/sweep-config.json"}
EOF
cd experiments
poetry run python src/generate_sweep_config.py <scratchpad>/sweep-spec.json
poetry run python src/experiment_runner.py <scratchpad>/sweep-config.json
ls <scratchpad>/sweep-results/meta_*.json
```

Expected: generated config validates + runs, ≥1 meta json. (`root_path` = e2e fixture input dir — adjust to merged-tree path from `tests/test_e2e_golden.py` if different.)
- [ ] **Step 3:** Interactive generator — import smoke only: `cd experiments && poetry run python -c "import sys; sys.path.insert(0, 'src'); import generate_experiment_config, generate_sweep_config; print('import ok')"` → `import ok`, no prompt fired. Full prompt-flow smoke was recorded in T22 PR — accept unless that PR note is missing (then NON-BLOCKING finding: rerun manually w/ user).
- [ ] **Step 4:** Dup-helper AC — `grep -rn "def discover_sources\|def filter_paths" experiments/src` → 1 definition each.

### Task 6: Aggregator (T23)

- [ ] **Step 1:** Requires sample analysis output (produced in Task 8 Step 1 — order OK if Task 8 run first; else run sample now). Scratch configs, both modes (absolute paths):

```bash
cat > <scratchpad>/agg-city.json <<'EOF'
{"metrics_json_path": "<abs experiments>/sample-experiment/results/sample-analysis/metrics-sample-experiment.json",
 "output_path": "<scratchpad>/agg_city.png", "group_by": "city"}
EOF
cat > <scratchpad>/agg-bucket.json <<'EOF'
{"metrics_json_path": "<abs same>",
 "output_path": "<scratchpad>/agg_bucket.png",
 "group_by": "instance_size_bucket"}
EOF
cd experiments/src
MPLBACKEND=Agg poetry run python aggregate_results.py <scratchpad>/agg-city.json
MPLBACKEND=Agg poetry run python aggregate_results.py <scratchpad>/agg-bucket.json
ls -l <scratchpad>/agg_*.png
```

Expected: 2 pngs exist, size > 0. (Field names per merged `AggregatorConfig` — re-derive if T23 Qs changed schema.)
- [ ] **Step 2:** No commented-out code — open `src/aggregate_results.py`, scan `grep -n "^#\|^ *#" src/aggregate_results.py` output → only real comments, zero code blocks; `grep -rn "from src\." experiments/src` → empty.
- [ ] **Step 3:** One aggregator — `ls experiments/src/aggregate*` → only `aggregate_results.py`; `ls archived_code/experiments/ | grep -i aggregate` → legacy + grouped present.

### Task 7: Error propagation (T24)

- [ ] **Step 1:** Corrupt-meta smoke (needs fresh sample results — Task 8 Step 1 or run now):

```bash
cd experiments/sample-experiment
M=$(find results -name 'meta_*.json' | head -1) && echo "corrupting $M"
echo '{broken' > "$M"
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./analyze.sh; echo exit=$?
```

Expected: metrics json contains failure row w/ `error_type` naming `$M`; stderr/log summary `1 of N`; `exit=1`; table still renders remaining rows.
- [ ] **Step 2:** Restore + clean rerun: `rm "$M"` then rerun `./run.sh` (re-solves the missing pair) + `./analyze.sh; echo exit=$?` → `exit=0`, no failure rows.
- [ ] **Step 3:** Greps — `grep -n "re.compile\|pattern.match" experiments/src/helpers/analyzers/analysis_table.py` → empty (no filename-as-schema); `grep -rn "return None" experiments/src/pipeline/analyzer_steps.py` → empty; `grep -rn "except Exception" experiments/src --include="*.py"` → only structured analyzer_steps + re-raising problem_runner.

### Task 8: Sample smoke + dead code + coverage (T25/T26 + refs)

- [ ] **Step 1:** Sample end-to-end (fresh):

```bash
cd experiments/sample-experiment && rm -rf results/*
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./run.sh
PATH="$(poetry -C .. env info --path)/bin:$PATH" ./analyze.sh
```

Expected metrics == frozen refs: APPROVAL 0.0033/219239/167; COST 0.0035/1.34763e11; COST_ORDINAL 0.0032/2.79444e11; bronowice 0.0666/4.35159e9. Drift = BLOCKING. Rerun `./run.sh` w/o rm → all "Found result" (cache hit).
- [ ] **Step 2:** Dead code (T25) — `cd experiments && poetry run ruff check --select F401 src` → clean; no `.ipynb`/`preflib` under src: `find src -name "*.ipynb"` → empty, `grep -rn "preflib" src --include="*.py"` → empty; `archived_code/` excluded everywhere: `grep -l "archived_code" ../.github/workflows/ruff.yml ../.pre-commit-config.yaml pyrightconfig.json` → all 3 hit.
- [ ] **Step 3:** Coverage (T26) — cache-hit-skips-solve: `poetry run pytest tests/test_problem_runner.py -q` → green. Module→test spot-audit:

```bash
cd experiments
for f in $(find src -name '*.py' ! -name '__init__.py'); do
  m=$(basename "$f" .py); grep -rlq "$m" tests || echo "UNCOVERED: $f"
done
```

Expected: no output (every module referenced by ≥1 test). Hits → cross-check T26 PR audit table before flagging (entrypoints may be covered via e2e import).

### Task 9: CI

- [ ] **Step 1:** `gh run list --branch feat/roadmap-base-branch --limit 5` → latest `completed success` (test ×3 projects, pyright ×3, build-bindings). Red → classify (Linux e2e tie-break = known risk → BLOCKING w/ own ticket).

### Task 10: Leftovers adjudication + verdict + commit

- [ ] **Step 1:** Adjudication table for T19–T26 leftover entries + Task 1 unresolved-questions audit + carried P1/P2 items (rc-tag rehearsal, repo archive, D12 residue, D14). Must cover: T19 golden regen justification present in history (single dedicated commit), stale pre-T19 results dirs note, T20 T26-prepaid tests, T25 untracked `.fleet/run.json`, metric-math findings from T26 (if any → explicit follow-ups exist?).
- [ ] **Step 2:** Write into `plans/leftovers.md`:

```markdown
### P3 judge verdict (<date>)

- **P3 VERIFIED COMPLETE @<commit> — GO for P4 (T27/T28).**  (or: **NO-GO — <blocking>**)
- Matrix: experiments <n> incl. e2e ×3 deterministic; core <n> / solvers <n>; ruff+format clean; pyright 0, disabled rules <before>→<after> vs T03 baseline (D12).
- ACs: broken-config ValidationError w/ field path; thin entrypoints (<wc numbers>); rename/pathlib/dead-code greps clean; generate→run OK; aggregator 2 modes → pngs; corrupt-meta → failure row + exit 1 / clean exit 0.
- Sample metrics == T01/T05 refs; cache-hit rerun OK; CI green.
- Findings: BLOCKING <none|list+tickets>; NON-BLOCKING <list>.
- Carried to P4/T28: <docs refs, rc-tag rehearsal, remaining suppressions, ...>.
```

- [ ] **Step 3:** Reconcile stale ROADMAP bookkeeping from Task 1.
- [ ] **Step 4:** `git add ROADMAP.md plans/leftovers.md && git commit -m "docs: P3 judge verdict — <GO|NO-GO>, findings recorded"` and push. NO other files.

## Unresolved questions

1. Interactive generator prompt-flow: accept T22 PR's recorded manual smoke + import/automated tests (plan default), or require a live human-driven prompt run in this session?
2. Frozen sample metrics refs assume T19–T26 stayed behavior-preserving on the sample (all plans claim so). If a P3 PR legitimately changed a ref (documented + golden-regen commit), judge against the updated ref from that PR — confirm this override rule.

## Steps

1. Task 1: preflight — merges, bookkeeping, unresolved-Qs audit list
2. Task 2: green matrix, e2e ×3 determinism, pyright ratchet accounting
3. Task 3: T19 broken-config feed + TypedDict/METADATA greps
4. Task 4: T20/T21 thin-entrypoint wc + pathlib/rename greps + roundtrip tests
5. Task 5: T22 sweep generate→run + import smoke + dup-helper grep
6. Task 6: T23 aggregator both modes → pngs + no-commented-code
7. Task 7: T24 corrupt-meta smoke (exit 1 / exit 0) + greps
8. Task 8: sample smoke vs frozen refs + T25 dead-code + T26 coverage audit
9. Task 9: CI green check
10. Task 10: adjudication, verdict entry, ROADMAP reconcile, docs commit
