from enum import Enum
from typing import List, Tuple, TypedDict, TypeAlias

Metric = Enum('Metric', ['NON_ZERO_OBJECTIVES', 'SUM_OBJECTIVES'])

NestedDict: TypeAlias = dict[str, str | 'NestedDict']


class AnalyzerResult(TypedDict):
    metrics: List[Metric]


