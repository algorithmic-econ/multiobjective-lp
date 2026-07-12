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
