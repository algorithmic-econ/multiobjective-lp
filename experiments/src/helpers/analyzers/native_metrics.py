"""Native metrics: C++ implementations from `muoblpbindings.metrics`.

Each has its own Metric name and a python counterpart (oracle) for parity
tests. Imports are lazy: python-only analysis works without the metrics
module, and a native request fails loudly with ImportError.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem

from helpers.analyzers.model import Metric

if TYPE_CHECKING:
    from muoblpbindings.metrics import SolvedInstance


def build_solved_instance(
    problem: MultiObjectiveLpProblem,
) -> "SolvedInstance":
    from muoblpbindings.metrics import SolvedInstance

    return SolvedInstance(problem)


def exclusion_ratio_native(instance: "SolvedInstance") -> dict:
    from muoblpbindings.metrics import exclusion_ratio

    # same inner key as python metric -> values compare directly
    return {"exclusion_ratio": exclusion_ratio(instance)}


NATIVE_STRATEGIES: dict[Metric, Callable[["SolvedInstance"], dict]] = {
    Metric.EXCLUSION_RATIO_NATIVE: exclusion_ratio_native,
}

# parity tests iterate this map: every native metric must be registered here
PYTHON_COUNTERPART: dict[Metric, Metric] = {
    Metric.EXCLUSION_RATIO_NATIVE: Metric.EXCLUSION_RATIO,
}
