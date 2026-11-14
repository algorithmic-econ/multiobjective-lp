# Extract analyzers → standalone package

## Context
experiments = opinionated harness. Other researchers bring own setup but want metrics standalone, same as solvers. → metrics = public library, not harness internals. Verdict: **yes, extract** the pure metric part.

## Scope split
- **Move to package:** `metrics.py`, `native_metrics.py`, `Metric` enum. Deps: `muoblp`, `validate_pb_constraint`, `muoblpbindings.metrics` (lazy import).
- **Stay in experiments:** `model.py` (AnalyzerConfig/Result/Failure, AggregatorConfig — import `runners.model`, pydantic), `analysis_table.py` (pandas table over result json), `analyzer_runner.py`.

## Key design points
- Folder `analyzers/`, dist + import `muoblpanalyzers` (mirrors `muoblpsolvers`).
- Deps: `muoblp`, `muoblpsolvers` (for `validate_pb_constraint`, `solvers/src/muoblpsolvers/election_solver.py:134`; decided: keep, no core change).
- bindings: optional extra `[native]` (native imports already lazy). Caveat: solvers already requires `muoblpbindings` → installed transitively anyway; extra still documents intent + pins version. Becomes meaningful if solvers ever drops hard bindings dep.
- Public API: `Metric`, `get_metrics(metrics, problem)`, per-metric fns (`exclusion_ratio`, `ejr_plus`, …), `PYTHON_COUNTERPART`. Replace if-chain w/ `PYTHON_STRATEGIES` dict.
- `Metric` values = on-disk keys (metrics.json, goldens) → unchanged.
- Packaging copies solvers policy: static `[project.dependencies]` pins + `[tool.poetry.dependencies]` path enrichment; experiments adds explicit path dep (transitive path issue).

## Unresolved questions
- Tests: move unit parts of `test_metrics.py`/`test_native_metrics.py` to package; e2e parity + goldens stay in experiments — answer: yes
- `muoblpsolvers` pin floor: published 0.0.15 must export `validate_pb_constraint` from `election_solver` — verify on PyPI wheel; else release solvers first. - answer: muoblpsolvers 0.0.15 are available on PyPi

## Steps
1. Scaffold `analyzers/` (pyproject, README, pyrightconfig, `src/muoblpanalyzers`, tests) mirroring `solvers/`.
2. Move `Metric` enum, `metrics.py`, `native_metrics.py`; registry dict replaces if-chain.
3. experiments: path dep on analyzers; `model.py`/`analyzer_runner.py`/tests import from `muoblpanalyzers`; delete moved files.
4. Move unit tests; keep e2e parity + golden in experiments.
5. CI/CD:
   - `publish.yml`: tag triggers + validate regex `(core|solvers|analyzers)@X.Y.Z(-rc)`; header comment. Build/publish jobs already generic (`PACKAGE_NAME` from tag, OIDC trusted publishing, `-rc` → TestPyPI) → no other change.
   - `test.yml`: `analyzers` in `test` + `pyright` matrices; `analyzers/poetry.lock` in both venv cache keys; bindings-wheel download/install steps `if: solvers || analyzers`.
   - `ruff.yml`: add `analyzers/` to `src`.
   - PyPI side (you): pending trusted publisher on pypi.org + test.pypi.org — project `muoblpanalyzers`, repo `algorithmic-econ/multiobjective-lp`, workflow `publish.yml`, no environment.
   - First release: tag `analyzers@0.0.1-rc` → TestPyPI smoke (`pip install muoblpanalyzers` in clean venv), then `analyzers@0.0.1`.
6. Docs: analyzers README, root README, CLAUDE.md repo structure (five projects).
7. Verify: `poetry run pytest` in solvers/analyzers/experiments; `pytest -m e2e` goldens identical; pyright 0; ruff clean.
