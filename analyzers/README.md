# Analyzers
Metrics for analysing solved multi objective linear programs
(`muoblp.MultiObjectiveLpProblem` with variable values set, e.g. by a solver
from `muoblpsolvers`).

---

## Installation
```shell
pip install muoblpanalyzers            # python metrics
pip install "muoblpanalyzers[native]"  # + C++ native metrics (muoblpbindings)
```

## Usage
```python
from muoblpanalyzers import Metric, get_metrics, ejr_plus

problem.solve(solver)  # any solved MultiObjectiveLpProblem

get_metrics([Metric.EXCLUSION_RATIO, Metric.EJR_PLUS_NATIVE], problem)
# {"EXCLUSION_RATIO": {"exclusion_ratio": 0.25}, "EJR_PLUS_NATIVE": {"ejr_plus": 0}}

ejr_plus(problem)  # single metric -> {"ejr_plus": 0}
```

## Metrics
`Metric` values are stable keys (used in persisted results), never renamed.

| `Metric` | Function | Result | Notes |
|---|---|---|---|
| `EXCLUSION_RATIO` | `exclusion_ratio` | `{"exclusion_ratio": float}` | share of objectives (voters) with value 0 |
| `SUM_OBJECTIVES` | `sum_objectives` | `{"sum": float}` | sum of objective values |
| `EJR_PLUS` | `ejr_plus` | `{"ejr_plus": int}` | unelected projects violating EJR+ (up to one) |
| `CONSTRAINTS` | `invalid_constraints` | `{"pb_constraint": bool, "invalid_count": int}` | needs PB constraint |
| `INSTANCE_SIZE` | `instance_size` | `{"size": int}` | number of variables |
| `TOTAL_COST` | `total_cost` | `{"total_cost": float}` | needs PB constraint |
| `EXCLUSION_RATIO_NATIVE` | native | same as `EXCLUSION_RATIO` | needs `[native]` |
| `EJR_PLUS_NATIVE` | native | same as `EJR_PLUS` | needs `[native]` |

PB constraint = single `<=` constraint covering all candidates
(`muoblpsolvers.election_solver.validate_pb_constraint`); missing or ambiguous
raises.

## Native metrics
C++ implementations from `muoblpbindings.metrics`, each a twin of a python
metric (`PYTHON_COUNTERPART`) with identical results (parity-tested, exact).
* Imports are lazy: python metrics work without bindings; a native metric
  without bindings raises `ImportError` (no silent python fallback).
* `get_metrics` builds one `SolvedInstance` handle per problem, shared by all
  requested native metrics; a snapshot of variable values at build time.

## Adding a metric
* Python: function `(MultiObjectiveLpProblem) -> dict` in `metrics.py`,
  `Metric` member in `metric.py`, entry in `PYTHON_STRATEGIES`.
* Native: follow "Adding new metric" in the
  [bindings README](../bindings/README.md), then register strategy in
  `NATIVE_STRATEGIES` and its python oracle in `PYTHON_COUNTERPART`
  (`native_metrics.py`). Parity tests pick it up from `PYTHON_COUNTERPART`.
* `experiments` consumers: add matching `AnalyzerResult` field
  (`experiments/src/helpers/analyzers/model.py`).

## Development
```shell
$ poetry install --all-extras
$ poetry run pytest
$ poetry run pyright
```
C++ edits need a reinstall of the bindings into this venv:
`poetry run pip install --force-reinstall --no-deps ../bindings`.
