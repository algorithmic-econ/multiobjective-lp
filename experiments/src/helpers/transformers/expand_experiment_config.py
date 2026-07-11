from helpers.runners.model import (
    CompactExperimentConfig,
    ExperimentConfig,
    RunnerConfig,
)


def expand_experiment_config(
    config: CompactExperimentConfig,
) -> ExperimentConfig:
    gen = config["runner_configs_generator"]
    extra: dict = {}
    if gen.get("constraints_configs_path"):
        extra["constraints_configs_path"] = gen["constraints_configs_path"]
    if gen.get("deduplicate_objectives"):
        extra["deduplicate_objectives"] = True
    runner_configs: list[RunnerConfig] = [
        {
            "solver_type": solver["type"],
            "solver_options": solver.get("options", {}),
            "source_type": gen["source_type"],
            "source_directory_path": source,
            "results_base_path": config["experiment_results_base_path"],
            **extra,
        }
        for source in gen["sources"]
        for solver in gen["solvers"]
    ]
    return {
        "concurrency": config["concurrency"],
        "experiment_results_base_path": config["experiment_results_base_path"],
        "runner_configs": runner_configs,
    }
