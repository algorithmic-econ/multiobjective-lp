import sys
from pathlib import Path

from generate_experiment_config import (
    build_runner_configs,
    discover_sources,
    filter_paths,
)
from helpers.runners.model import ExperimentConfig, Source, SweepSpec
from helpers.utils.utils import read_from_json, write_to_json


def generate_from_spec(spec: SweepSpec) -> ExperimentConfig:
    paths = discover_sources(spec.mode, spec.root_path)
    if spec.pattern_groups:
        paths = filter_paths(paths, spec.pattern_groups)

    return ExperimentConfig(
        concurrency=spec.concurrency,
        experiment_results_base_path=spec.experiment_results_base_path,
        runner_configs=build_runner_configs(
            paths,
            [(s.type, s.options) for s in spec.solvers],
            spec.utilities,
            Source.PABUTOOLS,
            spec.experiment_results_base_path,
            spec.constraints_configs_path,
            spec.deduplicate_objectives,
        ),
    )


def main(spec_path: Path) -> Path:
    spec = SweepSpec.model_validate(read_from_json(spec_path))
    config = generate_from_spec(spec)

    output_path = Path(spec.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_to_json(
        output_path, config.model_dump(mode="json", exclude_none=True)
    )
    return output_path


if __name__ == "__main__":
    generated = main(Path(sys.argv[1]))
    print(f"Generated sweep experiment configuration saved to {generated}")
