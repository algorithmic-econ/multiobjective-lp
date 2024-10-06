
from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem
from ..runners.model import Sources
from ..transformers.pabutools_transformer import pabutools_to_multiobjective_lp
from ..transformers.pabutools_utils import load_pabutools_by_district


def load_and_transform_strategy(source_type: Sources, source_directory_path: str) -> MultiObjectiveLpProblem:
    if source_type == Sources.PABUTOOLS:
        instances, profiles = load_pabutools_by_district(source_directory_path)
        return pabutools_to_multiobjective_lp(instances, profiles)
    raise Exception("Strategy not implemented for the source type")
