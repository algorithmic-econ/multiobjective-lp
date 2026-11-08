import logging

from muoblpanalyzers.metric import Metric
from muoblpanalyzers.metrics import (
    PYTHON_STRATEGIES,
    ejr_plus,
    exclusion_ratio,
    get_metric_strategy,
    get_metrics,
    instance_size,
    invalid_constraints,
    sum_objectives,
    total_cost,
)
from muoblpanalyzers.native_metrics import (
    NATIVE_STRATEGIES,
    PYTHON_COUNTERPART,
    build_solved_instance,
)

__all__ = [
    "NATIVE_STRATEGIES",
    "PYTHON_COUNTERPART",
    "PYTHON_STRATEGIES",
    "Metric",
    "build_solved_instance",
    "ejr_plus",
    "exclusion_ratio",
    "get_metric_strategy",
    "get_metrics",
    "instance_size",
    "invalid_constraints",
    "sum_objectives",
    "total_cost",
]

logger = logging.getLogger(__name__)

logger.addHandler(logging.NullHandler())
