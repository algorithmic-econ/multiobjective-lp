from enum import StrEnum


class Metric(StrEnum):
    # values are on-disk keys (metrics.json, goldens): never rename
    EXCLUSION_RATIO = "EXCLUSION_RATIO"
    SUM_OBJECTIVES = "SUM_OBJECTIVES"
    EJR_PLUS = "EJR_PLUS"
    CONSTRAINTS = "CONSTRAINTS"
    INSTANCE_SIZE = "INSTANCE_SIZE"
    TOTAL_COST = "TOTAL_COST"
    # native (C++ bindings) twin of EXCLUSION_RATIO
    EXCLUSION_RATIO_NATIVE = "EXCLUSION_RATIO_NATIVE"
    # native (C++ bindings) twin of EJR_PLUS
    EJR_PLUS_NATIVE = "EJR_PLUS_NATIVE"
