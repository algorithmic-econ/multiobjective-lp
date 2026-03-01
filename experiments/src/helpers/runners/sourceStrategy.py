from typing import List, Tuple

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from helpers.runners.model import Source, Utility
from helpers.transformers.pabutoolsToMoLp import (
    ConstraintConfig,
    pabutools_to_multi_objective_lp,
)
from helpers.transformers.pabutoolsUtils import (
    detect_utility_from_instances,
    load_pabutools_by_district,
)
from helpers.utils.utils import read_from_json


def load_and_transform_strategy(
    source_type: Source,
    utility_type: Utility | None,
    source_directory_path: str,
    constraints_config_path: str | None,
) -> Tuple[MultiObjectiveLpProblem, List[ConstraintConfig], Utility]:
    if source_type == "PABUTOOLS":
        instances, profiles = load_pabutools_by_district(source_directory_path)
        resolved_utility = (
            utility_type
            if utility_type is not None
            else detect_utility_from_instances(instances)
        )
        constraints_configs: List[ConstraintConfig] = (
            read_from_json(constraints_config_path)
            if constraints_config_path is not None
            else []
        )

        return (
            pabutools_to_multi_objective_lp(
                instances,
                profiles,
                constraints_configs,
                resolved_utility,
            ),
            constraints_configs,
            resolved_utility,
        )

    raise Exception("Strategy not implemented for the source type")
