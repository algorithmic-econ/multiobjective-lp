# Self-contained experiment example

---

### 1. Experiment is defined by configuration file

Experiment consists of set of runner configs, where, one runner config describes single instances of Multi-objective LP together with the input data.

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

* `solver_type: "MES_ADD1"` - which solver to use, see [solverStrategy.py](../src/helpers/runners/solverStrategy.py) for all values,
* `source_type: "PABUTOOLS"` - format and type of input data, see [sourceStrategy.py](../src/helpers/runners/sourceStrategy.py) for other values,
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
* `solver_options: ["use-gurobi"]` - optional parameter to provide configuration to selected solvers, e.g., Summing solver can internally use Gurobi instead of PULP

x
#### 1.3 [OPTIONAL] Constraints config

* Optional list of constraints applied to the Multi-objective LP.
* Provided inline via `constraints_configs` in runner config, or via file path in `constraints_configs_path`. Inline takes priority; if neither is set, no constraints are added.
* Each constraint is defined as:
  ```python
  Strategy = Literal["district_budget_minus_max", "category_vote_share", "category_cost_share"]

  class ConstraintConfig(TypedDict):
      key: Literal["CATEGORY", "DISTRICT"]
      value: str  # specific value or "*" for all
      bound: Literal["UPPER", "LOWER"]
      budget_ratio: NotRequired[float]
      strategy: NotRequired[Strategy]
  ```
* `value` can be a specific category/district name or `"*"` to generate constraints for all categories/districts.
* Either `budget_ratio` (fraction of total budget) or `strategy` (dynamically computed bound) must be provided.
* If given `value` is not present in the input data, the constraint is ignored.
* See [sample-constraints.jsonc](../resources/input/constraint-config/sample-constraints.jsonc) for a full example.
  ```json
  [
    {"key": "CATEGORY", "value": "education", "bound": "LOWER", "budget_ratio": 0.15},
    {"key": "DISTRICT", "value": "*", "bound": "LOWER", "strategy": "district_budget_minus_max"}
  ]
  ```

### 2. Input

* Input files are stored in directory `input`.
* Use provided pabutools link to download input data or use your own data.

### 3. Run experiment
```shell
$ cd {repository_root}/experiments/sample-experiment
$ ./run.sh
```

### 4. Results
* Results are stored under the path defined in the experiment config `experiment_results_base_path`
* Each Multi-objective LP instance generates two result files
  * Metadata and results file
  * LP definition file
  * Output files name have the following structure
    ```
    {file_type}_{unique_problem_id}_{source_directory_path_suffix}_{solver_type}.{extension}"
    ```
    Where
    * `file_type` is `problem` or `meta`
    * `unique_problem_id` is based on execution timestamp and UUID
    * `source_directory_path_suffix` and `solver_type` are based on experiment config file
    * `extension` is directly linked to `file_type`, it can be `.json` or `.lp`
  * Example files:
    * [problem_02-03T12-07-45_d757_warszawa_2024_MES.lp](results/partial–sample-experiment/problem_02-03T12-07-45_d757_warszawa_2024_MES.lp)
    * [meta_02-03T12-07-45_d757_warszawa_2024_MES.json](results/partial–sample-experiment/meta_02-03T12-07-45_d757_warszawa_2024_MES.json)


### 5. Define analyzer configuration
Analyzer configuration file defines (see [example](sample-analysis-config.jsonc)):
* Base path for saving analyzer results.
* Experiment results directory as data source (from previous steps).
* List of metrics to analyze.
```json
{
  "analyzer_result_path": "results/sample-analysis/",
  "experiment_results_base_path": "results/sample-experiment/",
  "metrics": ["EXCLUSION_RATION", "SUM_OBJECTIVES"]
}
```

### 6. Run analyzer
```shell
$ cd {repository_root}/experiments/sample-experiment
$ ./analyze.sh
```

Analyzer results are available at path provided in config `analyzer_result_path`
