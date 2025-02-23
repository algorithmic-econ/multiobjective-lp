# Self-contained experiment example

---

### 1. Experiment is defined by configuration file

Experiment consists of set of runner configs, where, one runner config describes single instances of Multi-objective LP together with the input data.

#### 1.1 Example [config](experiment-config.json) defines the following experiment: 
* `concurrency: 2`, number of problems from runner config list to run concurrently,
* `experiment_results_base_path: "results/sample-experiment/"`, path to directory where results are going to be saved,
* `"runner_configs": [{...}, ...]`, list of configurations describing instances of Multi-objective LP.

```json
{
  "concurrency": 2,
  "experiment_results_base_path": "results/sample-experiment/",
  "runner_configs": [
    {
      "solver_type": "MES",
      "source_type": "PABUTOOLS",
      "source_directory_path": "input/krakow_2024"
    },
    {
      "solver_type": "MES",
      "source_type": "PABUTOOLS",
      "source_directory_path": "input/warszawa_2024",
      "constraints_configs_path": "empty-constraints-config.json"
    }
  ]
}
```

#### 1.2 Single runner config defines the following problem and data:

* `solver_type: "MES"` - which solver to use, here it's MethodOfEqualShares solver, see [solverStrategy.py](../helpers/runners/solverStrategy.py) for other values,
* `source_type: "PABUTOOLS"` - format and type of input data, see [sourceStrategy.py](../helpers/runners/sourceStrategy.py) for other values,
* `source_directory_path: "input/krakow_2024"` - path to directory with input data, in this case to pabutools files describing PB instance.
* `constraints_configs_path: "empty-constraints-config.json"` - optional path to configuration file defining constraints for a problem
```json
{
  "solver_type": "MES",
  "source_type": "PABUTOOLS",
  "source_directory_path": "input/krakow_2024",
  "constraints_configs_path": "empty-constraints-config.json"
}
```

#### 1.3 [OPTIONAL] Constraints config file

* Optional list of constraints to be applied on the Multi-objective LP.
* Each constraint is defined as object:
  ```python
  class ConstraintConfig(TypedDict):
      type: Literal['CATEGORY']
      category: str
      bound: Literal['UPPER', 'LOWER']
      budget_ratio: float
  ```
* If given `category` value is not present, then the constraint will be ignored.
  ```json
  [
    {"type": "CATEGORY","category": "education", "bound": "LOWER", "budget_ratio": 0.15},
    {"type": "CATEGORY","category": "ignored", "bound": "UPPER", "budget_ratio": 0.30}
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
Analyzer configuration file defines (see [example](sample-analysis-config.json)):
* Base path for saving analyzer results.
* Experiment results directory as data source (from previous steps).
* List of metrics to analyze.
```json
{
  "analyzer_result_path": "results/sample-analysis/",
  "experiment_results_base_path": "results/sample-experiment/",
  "metrics": ["NON_ZERO_OBJECTIVES", "SUM_OBJECTIVES"]
}
```

### 6. Run analyzer
```shell
$ cd {repository_root}/experiments/sample-experiment
$ ./analyze.sh
```

Analyzer results are available at path provided in config `analyzer_result_path`

