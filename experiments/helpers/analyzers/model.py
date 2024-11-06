from enum import Enum
from typing import List, Tuple, TypedDict, TypeAlias

Metric = Enum('Metric', ['NON_ZERO_OBJECTIVES', 'SUM_OBJECTIVES'])


class AnalyzerResult(TypedDict):
    metrics: List[Metric]


