from typing import List, Tuple

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from helpers.transformers.pabutoolsToMoLp import (
    pabutools_to_multi_objective_lp,
    ConstraintConfig,
)

from helpers.transformers.pabutoolsUtils import load_pabutools_by_district
from helpers.utils.utils import read_from_json
from helpers.runners.model import Source, Utility


def load_and_transform_strategy(
    source_type: Source,
    utility_type: Utility,
    source_directory_path: str,
    constraints_config_path: str | None,
) -> Tuple[MultiObjectiveLpProblem, List[ConstraintConfig]]:
    if source_type == "PABUTOOLS":
        instances, profiles = load_pabutools_by_district(source_directory_path)
        constraints_configs: List[ConstraintConfig] = (
            read_from_json(constraints_config_path)
            if constraints_config_path is not None
            else []
        )

        return (
            pabutools_to_multi_objective_lp(
                instances, profiles, constraints_configs, utility_type
            ),
            constraints_configs,
        )

    raise Exception("Strategy not implemented for the source type")
