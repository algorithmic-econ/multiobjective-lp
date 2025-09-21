import re
from pathlib import Path

from helpers.utils.utils import write_to_json
from helpers.runners.model import Solver, Utility, RunnerConfig
from helpers.runners.model import ExperimentConfig


def generate_experiment_config(
    root_directory_path: str,
    regex_pattern: str,
    solvers: list[Solver],
    utilities: list[Utility],
    experiment_results_base_path: str,
    concurrency: int = 4,
    constraints_configs_path: str | None = None,
) -> ExperimentConfig:
    runner_configs: list[RunnerConfig] = []

    # Ensure root_directory_path is a Path object for easier manipulation
    root_path = Path(root_directory_path)

    for item_path in root_path.iterdir():
        if re.search(regex_pattern, item_path.name):
            for solver in solvers:
                for utility in utilities:
                    config: RunnerConfig = {
                        "solver_type": solver,
                        "solver_options": {},
                        "source_type": "PABUTOOLS",  # Hardcoded
                        "utility_type": utility,
                        "source_directory_path": str(item_path),
                        "constraints_configs_path": constraints_configs_path,
                        "results_base_path": experiment_results_base_path,
                    }

                    # TODO: MES_CONSTRAINT specific options
                    if solver == "MES_CONSTRAINT":
                        config["solver_options"] = {
                            "cost_modification_base": 1.007,
                            "max_iterations": 200,
                        }
                    if constraints_configs_path:
                        config["constraints_configs_path"] = (
                            constraints_configs_path
                        )

                    runner_configs.append(config)

    return {
        "concurrency": concurrency,
        "experiment_results_base_path": experiment_results_base_path,
        "runner_configs": runner_configs,
    }


if __name__ == "__main__":
    # Example usage:
    root_dir = "/Users/jasiek/Documents/Projects/pabulib"  # Replace with your actual root directory
    pattern = r"krakow"  # Regex to match 'krakow_2024'
    solvers_to_use: list[Solver] = ["MES_UTILS"]
    utilities_to_use: list[Utility] = ["COST"]

    # Optional: path to constraints config if MES_CONSTRAINT is used
    # constraints_path = (
    #     "../resources/input/constraint-config/sample-constraints.json"
    # )

    constraints_path = None

    generated_config = generate_experiment_config(
        root_dir,
        pattern,
        solvers_to_use,
        utilities_to_use,
        "../resources/experiment-results/",
        # constraints_configs_path=constraints_path,
    )

    # Output the generated configuration to a JSON file
    output_file_name = "generated_mes_experiment.json"
    write_to_json(output_file_name, generated_config)

    print(f"Generated experiment configuration saved to {output_file_name}")
