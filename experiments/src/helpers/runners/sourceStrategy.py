from pathlib import Path

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from helpers.runners.model import (
    ConstraintConfig,
    RunnerConfig,
    Source,
    Utility,
)
from helpers.transformers.pabutoolsToMoLp import (
    pabutools_to_multi_objective_lp,
)
from helpers.transformers.pabutoolsUtils import (
    detect_utility_from_instances,
    load_pabutools_by_district,
)
from helpers.utils.utils import read_from_json


def resolve_constraints_configs(
    config: RunnerConfig,
) -> list[ConstraintConfig]:
    if config.constraints_configs is not None:
        return config.constraints_configs
    path = config.constraints_configs_path
    if not path:
        return []
    return [
        ConstraintConfig.model_validate(entry)
        for entry in read_from_json(Path(path))
    ]


def load_and_transform_strategy(
    source_type: Source,
    utility_type: Utility | None,
    source_directory_path: str,
    constraints_configs: list[ConstraintConfig],
    deduplicate_objectives: bool,
) -> tuple[MultiObjectiveLpProblem, list[ConstraintConfig], Utility]:
    if source_type == "PABUTOOLS":
        instances, profiles = load_pabutools_by_district(source_directory_path)
        resolved_utility = (
            utility_type
            if utility_type is not None
            else detect_utility_from_instances(instances)
        )

        return (
            pabutools_to_multi_objective_lp(
                instances,
                profiles,
                constraints_configs,
                resolved_utility,
                deduplicate_objectives,
            ),
            constraints_configs,
            resolved_utility,
        )

    raise Exception("Strategy not implemented for the source type")
