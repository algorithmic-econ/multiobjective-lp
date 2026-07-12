# T02 action plan — tiny fixture + e2e golden test

## Context
P0 ticket after T01 (merged, PR #37). Goal: committed tiny pabulib fixture + pytest e2e golden test invoking runner+analyzer programmatically, guarding pipeline before refactors (T04+). Branch off `feat/roadmap-base-branch`, PR targets it. Repo GREEN after (pytest + ruff). `sample-experiment/` untouched (T09 territory). D11 (golden normalization field list) proposed in PR body.

## Env (from leftovers.md — do NOT recreate venv)
experiments venv = py3.12 w/ local `muoblpbindings` 0.0.17 build; machine CLT broken (can't rebuild bindings). `poetry -C` changes cwd — `cd experiments` first.

## Key facts (verified in source)
- `experimentRunner.main(config_dict)` (`src/experimentRunner.py:21`): mkdirs results path, injects `results_base_path` per runner_config, `Pool(processes=concurrency)` → `problem_runner`. No argparse coupling — call directly.
- `analyzerRunner.main(config_dict)` (`src/analyzerRunner.py:53`): iterdir `*.json` metas (fs-order!), HARDCODED `Pool(3)`, writes `{analyzer_result_path}metrics-{results_path.split('/')[-2]}.json` — both paths NEED trailing slash; also prints markdown table (harmless).
- 1 runner_config → 1 `problem_<MM-DDTHH-MM-SS_uuid4[:4]>_<srcbase>_<UTIL>_<SOLVER>.lp` + `meta_...json` (`problemRunner.py:79-94`). Meta: `time` (wall-clock), solver, solver_options, source_type, utility_type, source_path, constraints_configs, deduplicate_objectives, problem_path, instance_size, `selected` (SORTED).
- resultCache = results dir itself: matching meta present → solve SKIPPED, nothing written (`helpers/utils/resultCache.py`). Test must output to fresh `tmp_path` per run.
- GREEDY/MES_UTILS/MES_ADD1 take no solver_options (`solverStrategy.py:15-32`). MES via bindings needs int utilities — COST_ORDINAL = `int(cost)*(len(ballot)-idx)`, int ✓.
- Nondeterminism sources: ts+uuid filenames; `time`; analyzer iterdir row order; `os.listdir` in `helpers/transformers/pabutoolsUtils.py:55` (district merge order → LP var order → MES/greedy tie-breaks → `selected` may flip cross-machine); abs tmp paths in outputs; float `exclusion_ratio`.
- `analysis_table.py:31` regex parses meta filenames — basename `krakow_2024_mini` matches fine (lookahead tolerates underscores; COST_ORDINAL sorted len-desc). Post-T01 raises ValueError on miss — naming must stay regex-safe.
- pytest ini (`experiments/pyproject.toml`): only `pythonpath=["src"]`; no markers yet.
- pabulib parse: ballot referencing dropped project_id → KeyError; `min/max_length` NOT parse-enforced; MES drops zero-vote projects; district key = `meta["subunit"]`.

## Fixture (DECIDED: 2 districts + sort fix)
`experiments/tests/fixtures/input/krakow_2024_mini/poland_krakow_2024_{lagiewniki-borek-falecki,swoszowice}.pb` — trimmed from sample input (both 16-project districts, ordinal, 3-ranked ballots).

Trim rule per file (one-off scratchpad script, NOT committed; rule documented in `tests/fixtures/README.md`):
1. Keep top-5 projects by `votes` col (first 5 rows; pre-sorted). Bump to 6 if step 2 yields <15.
2. Keep first 15 ballots (file order) whose ALL 3 vote ids ⊆ kept projects. Filter-out, NOT truncate (truncation changes COST_ORDINAL weights + violates length meta).
3. Remap voter_id → district-prefixed (`d9_<id>`/`d10_<id>`) — `create_voter_objectives` keys by voter_id across districts; collisions merge voters silently.
4. META: `num_projects;5`, `num_votes;15`, `budget` ≈ 45% of sum(kept costs) (int) — forces proper-subset selection; keep vote_type/min_length/max_length/subunit/district.
5. Column layouts unchanged; note in README `votes`/`score`/`selected` cols stale (parser ignores).

Result: 10 projects / 30 voters / 2 districts. Exercises per-district budget caps + total constraint (`create_baseline_constraints` multi-district branch).

Sort fix: `pabutoolsUtils.py:55` `os.listdir(path)` → `sorted(os.listdir(path))`. 1-line, determinism prerequisite for AC + T03 CI; call out in PR (T01 B5 precedent).

## Test
`experiments/tests/test_e2e_golden.py`, `pytestmark = pytest.mark.e2e`, single test fn (one pipeline invocation: runner → meta asserts → analyzer → metrics asserts). Register marker in pyproject: `markers = ["e2e: end-to-end golden pipeline test"]`. Plain `pytest` also runs it (tiny, seconds); T03 CI uses `-m e2e`.

Configs inline dicts (no config files):
```python
SOLVERS = ["GREEDY", "MES_UTILS", "MES_ADD1"]
FIXTURE = Path(__file__).parent / "fixtures" / "input" / "krakow_2024_mini"
experiment = {
  "concurrency": 1,
  "experiment_results_base_path": f"{tmp_path}/results/",   # trailing slash!
  "runner_configs": [{
      "solver_type": s, "solver_options": {},
      "source_type": "PABUTOOLS", "utility_type": "COST_ORDINAL",
      "source_directory_path": str(FIXTURE),
      "constraints_configs": [],          # inline, skips path resolution
  } for s in SOLVERS],
}
analyzer = {
  "analyzer_result_path": f"{tmp_path}/analysis/",           # trailing slash!
  "experiment_results_base_path": f"{tmp_path}/results/",
  "metrics": ["EXCLUSION_RATION", "SUM_OBJECTIVES", "EJR_PLUS",
              "CONSTRAINTS", "INSTANCE_SIZE", "TOTAL_COST"],  # all impl'd; METADATA raises
}
```
Metrics file lands at `{tmp_path}/analysis/metrics-results.json` (`split('/')[-2]` = "results"). Pools accepted as-is (spawn-safe: module-level fns, dict configs, sys.path propagated); no monkeypatching.

## Golden + normalization (D11 proposal)
Committed (indent=2, sort_keys, trailing \n):
- `tests/fixtures/golden/selected.json` — `{solver: normalized_meta}` (full meta incl. selected/instance_size — richer than bare selected, still readable).
- `tests/fixtures/golden/metrics.json` — normalized analyzer rows array.

Normalization (`experiments/tests/golden_utils.py`):
1. Drop `time`.
2. Regex `(problem|meta)_\d{2}-\d{2}T\d{2}-\d{2}-\d{2}_[a-zA-Z0-9]{4}_` → `\1_ID_` in `problem_path`.
3. Paths → basename only (`problem_path`, `source_path`) — kills tmp_path/abs paths.
4. Floats recursively rounded to 6 dp (`exclusion_ratio`; no-op on ints).
5. Metrics rows: assert no `None` rows (fail loudly), sort by `solver`.
Compare parsed objects (`assert normalized == golden`) → pytest `-vv` dict diff readable.

Regen: `UPDATE_GOLDEN=1 poetry run pytest -m e2e` writes goldens then `pytest.fail("golden regenerated — inspect + commit separately")` (fail-not-pass: env leak can't green CI). Documented in README + docstring.

## Bootstrap sanity (before committing goldens)
Each solver `selected` nonempty proper subset of 10; `instance_size` 10; ideally GREEDY ≠ MES sets; `exclusion_ratio` ∈ (0,1); no None rows. Degenerate → retune budgets, regen.

## Verification
1. `cd experiments && poetry run pytest -m e2e` ×3 consecutive — green (AC determinism).
2. Mutation (AC): `greedy_solver.py:47` `reverse=True→False` → e2e FAILS w/ readable diff; revert. `mes/mes_add1.py:41` budget→`total_budget // 2` → MES_ADD1 fails; revert. `git diff` clean after.
3. `poetry run pytest` — full suite green.
4. `poetry run ruff format --check . && poetry run ruff check .` — green.

## Risks
- <15 qualifying ballots for top-5 → bump K to 6–7 (~10 projects tolerance OK).
- Budget tuning 1–2 iterations for discriminating selection.
- C++ MES tie-breaking cross-platform: goldens macOS-generated, could differ on Linux CI → surfaces in T03; sort fix removes main known cause; residual accepted.
- spawn edge case under pytest: unlikely; fallback = call `problem_runner` per config directly (test-side only).

## Deliverables
Branch `feat/t02-e2e-golden` off `feat/roadmap-base-branch`; PR → `feat/roadmap-base-branch` w/ D11 list in body; tick ROADMAP T02 + PR link; append leftovers.md.

## Resolved decisions
1. Fixture: 2 districts + `sorted(os.listdir)` 1-liner (user-confirmed).
2. Golden = full normalized meta per solver + metrics rows (not bare selected lists).
3. Trim script one-off, rule in README; no committed generator.
4. Float precision: 6 dp.
5. Mutation check manual, procedure in fixture README; not automated.
6. e2e in default `pytest` run + `-m e2e` selectable.

## Unresolved questions
None blocking. D11 exact list confirmed in PR review by design (roadmap §6).

## Steps
1. Branch `feat/t02-e2e-golden` off `feat/roadmap-base-branch`.
2. Scratchpad trim script → 2 trimmed `.pb`; eyeball vs trim rules.
3. Commit `tests/fixtures/input/krakow_2024_mini/*.pb` + `tests/fixtures/README.md` (provenance, trim rule, regen + mutation-check instructions).
4. `sorted(os.listdir(path))` in `src/helpers/transformers/pabutoolsUtils.py:55`.
5. `tests/golden_utils.py` (normalize meta/metrics, UPDATE_GOLDEN write+fail).
6. `tests/test_e2e_golden.py` (configs above; runner main → meta asserts → analyzer main → metrics asserts).
7. Register `e2e` marker in `experiments/pyproject.toml`.
8. `UPDATE_GOLDEN=1 pytest -m e2e` → goldens; bootstrap sanity; commit goldens separately.
9. Verification 1–4 (3× runs, 2 mutations+revert, full pytest, ruff).
10. PR → `feat/roadmap-base-branch` (D11 proposal in body); tick ROADMAP T02; append leftovers.md.
