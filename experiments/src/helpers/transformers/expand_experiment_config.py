from helpers.runners.model import (
    CompactExperimentConfig,
    ExperimentConfig,
    RunnerConfig,
)


def parse_experiment_config(
    data: dict | ExperimentConfig | CompactExperimentConfig,
) -> ExperimentConfig:
    """Single config-load boundary: validates + expands compact form."""
    if isinstance(data, ExperimentConfig):
        return data
    if isinstance(data, CompactExperimentConfig):
        return expand_experiment_config(data)
    if data.get("compact_config"):
        return expand_experiment_config(
            CompactExperimentConfig.model_validate(data)
        )
    return ExperimentConfig.model_validate(data)


def expand_experiment_config(
    config: CompactExperimentConfig,
) -> ExperimentConfig:
    gen = config.runner_configs_generator
    runner_configs = [
        RunnerConfig(
            solver_type=solver.type,
            solver_options=solver.options,
            source_type=gen.source_type,
            source_directory_path=source,
            results_base_path=config.experiment_results_base_path,
            constraints_configs_path=gen.constraints_configs_path,
            deduplicate_objectives=gen.deduplicate_objectives,
        )
        for source in gen.sources
        for solver in gen.solvers
    ]
    return ExperimentConfig(
        concurrency=config.concurrency,
        experiment_results_base_path=config.experiment_results_base_path,
        runner_configs=runner_configs,
    )
