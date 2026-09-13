# EXPERIMENTS

This directory is self-contained and includes source code and resources required to run experiments and analyze the results.

---

## Initial Setup

Requires Python 3.13, Poetry 2.x and a C++20 toolchain. `core`, `solvers` and
`bindings` are path dependencies, installed from this repository (bindings are
compiled on install, see [bindings README](../bindings/README.md)).
```shell
$ cd multiobjective-lp/experiments # package root
$ poetry install
```

## Example experiment
Follow [sample experiment](sample-experiment/README.md) for instructions
on how to set up and run multi objective LP experiment with a MES solver and two instances of PB.

## Entrypoints
Scripts in `src/`, run with `poetry run python src/<script> <config>`. Config
schemas are Pydantic models in `src/helpers/runners/model.py` and
`src/helpers/analyzers/model.py`.

| Script | Argument | Config model |
|---|---|---|
| `experiment_runner.py` | experiment config | `ExperimentConfig` / `CompactExperimentConfig` |
| `analyzer_runner.py` | analyzer config (exit 1 on any failed analysis) | `AnalyzerConfig` |
| `aggregate_results.py` | aggregator config → plot | `AggregatorConfig` |
| `generate_sweep_config.py` | sweep spec → experiment config | `SweepSpec` |
| `generate_experiment_config.py` | none, interactive prompts (needs TTY) | — |

Relative paths in configs resolve against the current working directory.

## Development
```shell
$ poetry run pytest          # unit tests + e2e golden
$ poetry run pytest -m e2e   # e2e golden only
$ poetry run pyright
```
* e2e golden test runs the pipeline on a tiny fixture and compares with
  committed goldens; normalization in `tests/golden_utils.py`, fixture and
  regeneration rules in [tests/fixtures/README.md](tests/fixtures/README.md).
* `archived_code/` holds dead code kept for reference; excluded from ruff and
  pyright.
* `src/helpers/transformers/preflib_to_muoblp.py` is staged, not yet wired
  code (future PREFLIB source) — not dead.
