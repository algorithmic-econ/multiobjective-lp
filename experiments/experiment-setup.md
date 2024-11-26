## Experiment preparation steps

This repository contains sample directory structure for running experiments.  
However, you can use **any structure by providing different paths** in configuration 

### 1. Define experiment by creating configuration file, with the following structure
```json
{
  "experiment_results_base_path": "resources/experiment-results/sample/",
  "runner_configs": ["RunnerConfig"]
}
```
where `RunnerConfig` is an object with structure 
```json
{
  "solver_type": "SUMMING",
  "source_type": "PABUTOOLS",
  "source_directory_path": "resources/input/krakow_2023/",
  "constraints_configs_path": "resources/input/constraint-config/no-constraints.json"
}
```
Check the source code for available solvers and supported source types.

Constraints config is optional. If provided, it should have the following structure:
```json
[
  {"type": "CATEGORY","category": "education", "bound": "LOWER", "budget_ratio": 0.15},
  {"type": "CATEGORY","category": "ignored", "bound": "UPPER", "budget_ratio": 0.30}
]
```
If the provided `category` is not present for a given election, the constraint will be ignored.

[See sample configuration here](resources/input/experiment-config/sample-experiment.json)

### 2. Run experiment script, the only input is path to configuration file
```shell
python experimentRunner.py {EXPERIMENT_CONFIG_PATH}
# Example:
# cd {repository_root}/experiments
# python experimentRunner.py resources/input/experiment-config/sample-experiment.json 
```

In the code of `experimentRunner` you can configure concurrency level
```python
# Example processing with 4 threads
with multiprocessing.Pool(processes=4) as pool:
```

### 3. Experiment results
Assuming sample directory structure in this repository, running experiment script will generate following files:
For each `RunnerConfig` there are two result files created.
```shell
problem_${TIMESTAMP_UNIQUE_ID}.lp
run_${TIMESTAMP_UNIQUE_ID}.json
```

Run metadata is stored in `run_*.json`
```json
{
    "time": float,
    "solver": Solver,
    "source_type": Source,
    "source_path": str,
    "constraints_configs": List[ConstraintConfig],
    "problem_path": str
    "selected": List[str],
}
```
Including `problem_path` pointing to the second file.
Additionally `selected` is a list of binary variables names representing chosen candidates.
It is used when running analyzer to measure selected metrics.

The second file `problem_*.lp` is serialized LP problem with additional `OBJECTIVES` section.
To read it use `read_lp_file` method
```python
from multiobjective_lp.utils.lpReaderUtils import read_lp_file
```

### 4. Analyze results
TBD
