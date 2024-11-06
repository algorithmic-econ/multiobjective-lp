from typing import List, Tuple
from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem
from ..runners.model import Source
from ..transformers.pabutoolsToMoLp import pabutools_to_multi_objective_lp, ConstraintConfig
from ..transformers.pabutoolsUtils import load_pabutools_by_district
from ..utils.utils import read_from_json


def load_and_transform_strategy(source_type: Source,
                                source_directory_path: str,
                                constraints_config_path: str | None) \
        -> Tuple[MultiObjectiveLpProblem, List[ConstraintConfig]]:
    if source_type == 'PABUTOOLS':
        instances, profiles = load_pabutools_by_district(source_directory_path)
        constraints_configs: List[ConstraintConfig] = read_from_json(constraints_config_path) \
            if constraints_config_path is not None else []

        return pabutools_to_multi_objective_lp(instances, profiles, constraints_configs), constraints_configs

    raise Exception("Strategy not implemented for the source type")
