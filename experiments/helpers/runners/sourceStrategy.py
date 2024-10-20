
from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem
from ..runners.model import Sources
from ..transformers.pabutoolsToMoLp import pabutools_to_multi_objective_lp
from ..transformers.pabutoolsUtils import load_pabutools_by_district


def load_and_transform_strategy(source_type: Sources, source_directory_path: str) -> MultiObjectiveLpProblem:
    if source_type == Sources.PABUTOOLS:
        instances, profiles = load_pabutools_by_district(source_directory_path)
        return pabutools_to_multi_objective_lp(instances, profiles)
    raise Exception("Strategy not implemented for the source type")
