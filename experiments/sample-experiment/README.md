# Self-contained experiment example

---

### 0. Setup

Requires Python 3.13, Poetry 2.x and a C++20 toolchain (bindings are built
from source, see [bindings README](../../bindings/README.md)).

```shell
$ cd {repository_root}/experiments
$ poetry install
```

### 1. Experiment is defined by configuration file

Experiment consists of set of runner configs, where, one runner config describes single instances of Multi-objective LP together with the input data.
Config schema = Pydantic models in [model.py](../src/helpers/runners/model.py); unknown keys are rejected.

#### 1.1 Example [config](experiment-config.jsonc) defines the following experiment:
* `concurrency: 3`, number of problems from runner config list to run concurrently,
* `experiment_results_base_path: "results/sample-experiment/"`, path to directory where results are going to be saved,
* `"runner_configs": [{...}, ...]`, list of configurations describing instances of Multi-objective LP.

```json
{
  "concurrency": 3,
  "experiment_results_base_path": "results/sample-experiment/",
  "runner_configs": [
    {
      "solver_type": "MES_ADD1",
      "source_type": "PABUTOOLS",
      "utility_type": "COST",
      "source_directory_path": "input/krakow_2024"
    },
    {
      "solver_type": "MES_ADD1",
      "source_type": "PABUTOOLS",
      "utility_type": "COST_ORDINAL",
      "source_directory_path": "input/krakow_2024",
      "constraints_configs_path": "empty-constraints-config.jsonc"
    }
  ]
}
```

#### 1.2 Single runner config defines the following problem and data:

* `solver_type: "MES_ADD1"` - which solver to use: `GREEDY`, `PHRAGMEN`, `SUMMING`, `MES_ADD1`, `MES_UTILS`, `MES_CONSTRAINT`, `MES_EXPONENTIAL`, `STV`, `EXPANDING_APPROVALS`, `SOLID_COALITION_REFINEMENT` (see [solver_strategy.py](../src/helpers/runners/solver_strategy.py)),
* `source_type: "PABUTOOLS"` - format and type of input data, see [source_strategy.py](../src/helpers/runners/source_strategy.py) for other values,
* `utility_type: "COST"` - optional utility function type (`COST`, `APPROVAL`, `ORDINAL`, `CUMULATIVE`, `COST_ORDINAL`, `COST_CUMULATIVE`), auto-detected from input if omitted,
* `source_directory_path: "input/krakow_2024"` - path to directory with input data, or path to single `.pb` file,
* `constraints_configs_path: "empty-constraints-config.jsonc"` - optional path to constraints config file (see 1.3),
* `constraints_configs: [...]` - optional inline constraints list, alternative to file path (see 1.3). Inline takes priority over file path.
```json
{
  "solver_type": "MES_ADD1",
  "source_type": "PABUTOOLS",
  "utility_type": "COST",
  "source_directory_path": "input/krakow_2024",
  "constraints_configs_path": "empty-constraints-config.jsonc"
}
```

##### Optional runner configuration
* `solver_options: {...}` - solver constructor kwargs, e.g., `{"use_gurobi": true}` for `SUMMING`, `{"kappa": 0.0}` for `PHRAGMEN`, `{"budget_init": 1000}` for `MES_EXPONENTIAL` (required there). See [solvers README](../../solvers/README.md#solvers) for all options.
* `deduplicate_objectives: false` - merge identical voter objectives into one weighted objective.
* `results_base_path` - override `experiment_results_base_path` for this runner config.

##### Compact config
Instead of listing `runner_configs`, set `"compact_config": true` and provide
`runner_configs_generator` (`solvers`, `source_type`, `sources`, optional
`constraints_configs_path`, `deduplicate_objectives`); runner configs are
expanded from it (`CompactExperimentConfig` in [model.py](../src/helpers/runners/model.py)).

#### 1.3 [OPTIONAL] Constraints config

* Optional list of constraints applied to the Multi-objective LP.
* Provided inline via `constraints_configs` in runner config, or via file path in `constraints_configs_path`. Inline takes priority; if neither is set, no constraints are added.
* Each constraint (`ConstraintConfig`) has fields:
  * `key`: `"CATEGORY"` or `"DISTRICT"`
  * `value`: specific category/district name or `"*"` for all
  * `bound`: `"UPPER"` or `"LOWER"`
  * `budget_ratio` (optional float): fraction of total budget
  * `strategy` (optional): dynamically computed bound, `district_budget_minus_max`, `category_vote_share` or `category_cost_share`
* Either `budget_ratio` or `strategy` must be provided.
* If given `value` is not present in the input data, the constraint is ignored.
  ```json
  [
    {"key": "CATEGORY", "value": "education", "bound": "LOWER", "budget_ratio": 0.15},
    {"key": "DISTRICT", "value": "*", "bound": "LOWER", "strategy": "district_budget_minus_max"}
  ]
  ```

### 2. Input

* Input files are stored in directory `input`.
* Source pabulib links are in `input/*/link.txt`; download other instances there or use your own data.

### 3. Run experiment
```shell
$ cd {repository_root}/experiments/sample-experiment
$ poetry run sh run.sh
```

### 4. Results
* Results are stored under the path defined in the experiment config `experiment_results_base_path` (gitignored)
* Each Multi-objective LP instance generates two result files
  * Metadata and results file
  * LP definition file
  * Output files name have the following structure (see [result_naming.py](../src/helpers/utils/result_naming.py))
    ```
    {file_type}_{problem_id}_{data_source}_{utility_type}_{solver_type}.{extension}
    ```
    Where
    * `file_type` is `problem` or `meta`
    * `problem_id` is based on execution timestamp and UUID
    * `data_source` is the last segment of `source_directory_path` (without `.pb`)
    * `utility_type` and `solver_type` are based on runner config
    * `extension` is directly linked to `file_type`, it can be `.json` or `.lp`
  * Example files:
    ```
    problem_08-30T18-45-11_6305_krakow_2024_COST_MES_ADD1.lp
    meta_08-30T18-45-11_6305_krakow_2024_COST_MES_ADD1.json
    ```
* Rerun skips already-solved problems (result cache); delete `results/` to force re-solve.


### 5. Define analyzer configuration
Analyzer configuration file defines (see [example](sample-analysis-config.jsonc)):
* `analyzer_result_path` - base path for saving analyzer results.
* `experiment_results_base_path` - experiment results directory as data source (from previous steps).
* `metrics` - list of metrics: `EXCLUSION_RATION`, `SUM_OBJECTIVES`, `EJR_PLUS`, `CONSTRAINTS`, `INSTANCE_SIZE`, `TOTAL_COST`.
* `concurrency` - optional number of worker processes (default `3`).
```json
{
  "analyzer_result_path": "results/sample-analysis/",
  "experiment_results_base_path": "results/sample-experiment/",
  "metrics": ["EXCLUSION_RATION", "SUM_OBJECTIVES", "EJR_PLUS", "INSTANCE_SIZE", "TOTAL_COST"]
}
```

### 6. Run analyzer
```shell
$ cd {repository_root}/experiments/sample-experiment
$ poetry run sh analyze.sh
```

Analyzer results are available at path provided in config `analyzer_result_path`.
Exit code is `1` if any result failed to analyze (failures are listed in the output).

### 7. Aggregate (plot)
Aggregator config (`AggregatorConfig` in [analyzers/model.py](../src/helpers/analyzers/model.py)):
* `metrics_json_path` - analyzer output json, `output_path` - plot `.png`
* `group_by`: `"city"` or `"instance_size_bucket"` (needs `INSTANCE_SIZE` metric)
* optional: `bucket_size` (10), `exclude_cities`, `include_solvers`, `normalize_baseline` (bucket mode, solver type), `clip_upper` (5.0)

```json
{
  "metrics_json_path": "results/sample-analysis/metrics-sample-experiment.json",
  "output_path": "results/sample-plot.png",
  "group_by": "instance_size_bucket",
  "bucket_size": 50,
  "normalize_baseline": "MES_ADD1"
}
```
```shell
$ cd {repository_root}/experiments/sample-experiment
$ poetry run python ../src/aggregate_results.py aggregator-config.json
```
