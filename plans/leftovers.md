## Leftovers

Use this file as a memory between sessions that implement independent tasks
---

### From T01 (PR #37, 2026-07-12)

Env / machine state (NOT in repo):
- experiments venv = py3.12 (`poetry env use /opt/homebrew/bin/python3.12`). T04 bumps to 3.13.
- PyPI `muoblpbindings` stale (0.0.16, lacks `expanding_approvals`/`stv`/`scr`) → `import muoblpsolvers` fails from clean install. Workaround baked into current venv: local build of sibling repo `../muoblpbindings` (0.0.17) via `pip install --ignore-requires-python` (repo requires py>=3.13). Any fresh venv before T04/T06 needs same step.
- THIS MACHINE: CommandLineTools broken — toolchain missing `c++/v1` headers, bare `clang++` can't compile hello-world. Bindings build needs `SDKROOT=$(xcrun --show-sdk-path) CXXFLAGS="-cxx-isystem $SDKROOT/usr/include/c++/v1"`. Proper fix: reinstall CLT (`xcode-select --install`, needs user). Affects T06/T07 local verify.

Discovered bugs fixed in T01 beyond plan (context for T02 golden):
- B6: non-dedup objective weights must be int (`1` not `1.0`) — MES bindings take `long long` utilities, pybind rejects float. Dedup path uses `len()` (int) already. If anyone reintroduces float weights/utilities, every MES solve dies with pybind TypeError.
- B7: runner must call `problem.write_lp` (custom, appends OBJECTIVES/WEIGHTS) not pulp `writeLP` — analyzer `read_lp_file` requires those sections. Contract covered by `tests/test_lp_roundtrip.py`.

Deferred (has ticket):
- Analyzer `except → None` swallows real errors (made B7 diagnosis painful) → T24.
- `config/logging_config.yaml` FileNotFoundError noise when scripts run from `sample-experiment/` (relative path from cwd); non-fatal → T20/T09.
- `analysis_table` KeyError `Location-Year` when ALL rows fail regex (empty df) — only partial fix done (ValueError w/ pattern) → T24.
- Stale tracked generated file `sample-experiment/results/sample-analysis/metrics-sample-experiment.jsonc` (old ext; new pipeline writes `.json`, which is untracked) → prune in T09.
- MES_CONSTRAINT/MES_EXPONENTIAL/PHRAGMEN with empty `solver_options` still crash inside `actualSolve` (missing `max_iterations` etc.) → T10/T13.

Facts useful for T02 (golden e2e):
- Sample run: 4 configs (all MES_ADD1), full krakow_2024 = 19 districts, ~2 min wall on this machine; analyze ~1 min.
- Reference metrics from T01 verify run (exclusion_ratio / sum_obj / ejr+): APPROVAL 0.0033/219239/167; COST 0.0035/134763199377/0; COST_ORDINAL 0.0032/279444152847/0; bronowice COST_ORDINAL 0.0666/4351588280/0.
- Meta json `time` field + filename timestamp+uuid are nondeterministic → normalization list (D11).
- pulp preserves int coefficients in `LpAffineExpression` (verified) — int utilities survive to bindings.

Repo conventions observed:
- pre-commit hooks active (ruff, ruff-format, eof, trailing-ws) — commits auto-checked.
- `poetry -C <dir> run` changes cwd → breaks relative-path scripts; `cd` first instead.
- Branch naming used: `feat/t01-fix-pipeline` (existed already; plan's `fix/...` name skipped).

### From T02 (PR #38, 2026-07-12)

- e2e golden: `cd experiments && poetry run pytest -m e2e`; regen `UPDATE_GOLDEN=1 ...` (writes goldens then FAILS by design — inspect + commit separately). Normalization list (D11) in `tests/golden_utils.py`, awaiting confirm in PR #38 review.
- Goldens macOS-generated; C++ MES tie-breaks may differ on Linux CI → surfaces in T03; `sorted(os.listdir)` fix removed main known cause.
- DISCOVERED: GreedySolver `total_utility[candidate]` KeyError on zero-vote candidates (`greedy_solver.py:43`; full krakow never hits it). Fixture avoids via coverage-first ballot pick. Fix in T13 (validation) or T17 (tests).
- DISCOVERED: meta `instance_size`=11 not 10 — pulp `__dummy` passes `problemRunner.py` filter `name != "dummy"` (actual name `__dummy`). Metric INSTANCE_SIZE correct (10). Golden captures 11; fix in T19 (meta remodel) → goldens regen there.
- MES_ADD1 golden has `invalid_count: 1` — Add1 exceeds district cap by design, not a bug.
- `pytest.register_assert_rewrite("tests.golden_utils")` needed in conftest for readable golden diffs (+ E402 per-file-ignore); pattern applies to any future assert-helper module.
- tests/ is a package (relative imports, `tests.golden_utils` module path).

### From T03 (PR #39, 2026-07-12)

Env / machine state (NOT in repo):
- experiments now py3.13; venv `muoblpexp-*-py3.13` (poetry cache, not in-project locally). Lock regenerated → `muoblpbindings` 0.0.17 resolved from **PyPI** (macos-arm64 wheel). T01 local-build-of-sibling-repo hack now OBSOLETE for experiments. Transitive bumps accepted silently (notebook 7.6.0, coverage 7.15.0, etc.).
- core + solvers venvs also recreated on 3.13 (`poetry env use /opt/homebrew/bin/python3.13`). core pyproject still `requires-python >=3.11` (T04 bumps to >=3.13); CI runs 3.13 which satisfies it.
- core got a **dev group** (pytest, pyright) — previously none; core had no tests dir (pytest exit-5). Added `core/tests/test_import.py` smoke test.

pyright suppression inventory (D12 ratchet backlog — all basic mode):
- **core**: 1 inline `# pyright: ignore[reportInvalidTypeForm]` in `multi_objective_lp.py:16` (`sense: LpMaximize|LpMinimize` — pulp consts are ints not types; real fix T27).
- **solvers**: config `reportArgumentType: none` (15 systemic errors — `Utility`/int + float/int + dict-value invariance across mes_add1, mes_constrains, mes_exponential, mes_utility, phragmen). Plus 2 inline: `mes_constrains.py:21` reportOptionalOperand (Optional `constraint.value()`; None-guard T13), `phragmen.py:398` reportReturnType (returns list, annotated set[str]; T16/T27).
- **experiments**: config disables 10 rules (reportArgumentType 31, reportCallIssue 7, reportAttributeAccessIssue 7, reportAssignmentType 7, reportOperatorIssue 6, reportOptionalSubscript 5, reportReturnType 4, reportGeneralTypeIssues 3, reportTypedDictNotRequiredAccess 3, reportInvalidTypeForm 3 = 76 total). Loose pabutools/pandas interop + tests; most files rewritten in Phase 3 (T19 Pydantic, T21 rename, T22/T23 consolidate, T25 dead-code) which should eliminate most — re-enable rules incrementally as Phase 3 lands.

CI (test.yml) notes for T07/future:
- Rewrote: 3-project matrix (core/solvers/experiments) × {test, pyright} jobs, py3.13, `fail-fast: false`. Cache path per-project `${{ matrix.project }}/.venv`, key hashes all 3 locks (path-dep interdependence). No path filters; push trigger limited to `main` + `feat/roadmap-base-branch`; PRs always run.
- **UNVERIFIED locally: Linux CI e2e golden** — goldens macOS-generated; MES C++ tie-break divergence risk (leftovers T02). If ubuntu e2e diffs: normalization fix (`experiments/tests/golden_utils.py`) or switch experiments matrix to `macos-15` + GH issue. NO golden regen.
- `poetry install` runs unconditionally (no cache-hit guard) so editable path-deps (core←solvers←experiments) re-link against checkout.

### From T04 (PR #40, 2026-07-12)

- Trivial ticket — T03 had done most. Only 3 source edits: `core/pyproject.toml` requires-python `>=3.11`→`>=3.13`, `publish.yml:29` setup-python `3.12`→`3.13`, relock ×3.
- Relock diffs MINIMAL, zero transitive bumps: core lock `[metadata] python-versions`→`>=3.13` + content-hash; solvers/experiments only the `muoblp` path-dep `python-versions`→`>=3.13`. (No `poetry install` changes — all venvs already 3.13 from T03.)
- All green locally: pytest core 1 / solvers 13 / experiments 75 (incl e2e golden, no regen), ruff clean, pyright 0 errors ×3. pyright suppression inventory (T03 D12 backlog) unchanged.
- publish.yml change NOT CI-verifiable (tag-triggered) — review-only, rc-tag dry run deferred to T08.
