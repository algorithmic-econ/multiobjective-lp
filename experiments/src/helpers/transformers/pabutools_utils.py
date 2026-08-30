from typing import TypeAlias
import os
from pabutools.election import Instance, Profile, parse_pabulib

from helpers.runners.model import Utility

District: TypeAlias = str
AgentId: TypeAlias = str

_VOTE_TYPE_TO_UTILITY: dict[str, Utility] = {
    "approval": Utility.COST,
    "ordinal": Utility.COST_ORDINAL,
    "cumulative": Utility.COST_CUMULATIVE,
    "choose-1": Utility.COST,
}


def detect_utility_from_instances(
    instances: dict[District, Instance],
) -> Utility:
    vote_types = set()
    for instance in instances.values():
        meta = instance.meta or {}
        if "vote_type" not in meta:
            raise ValueError(f"Instance missing vote_type in meta: {meta}")
        vote_types.add(meta["vote_type"])

    if len(vote_types) > 1:
        raise ValueError(
            f"Inconsistent vote_types across districts: {vote_types}"
        )

    vote_type = vote_types.pop()
    if vote_type not in _VOTE_TYPE_TO_UTILITY:
        raise NotImplementedError(
            f"vote_type '{vote_type}' has no utility mapping"
        )

    return _VOTE_TYPE_TO_UTILITY[vote_type]


def load_pabutools_by_district(
    path: str,
) -> tuple[dict[District, Instance], dict[District, Profile]]:
    instances: dict[District, Instance] = {}
    profiles: dict[District, Profile] = {}

    relevant_files: list[str] = []
    if os.path.isfile(path) and path.endswith(".pb"):
        relevant_files.append(path)

    if os.path.isdir(path):
        # sorted: os.listdir order is fs-dependent; district order defines LP
        # var order -> solver tie-breaks -> nondeterministic `selected`
        for filename in sorted(os.listdir(path)):
            if filename.endswith(".pb"):
                relevant_files.append(os.path.join(path, filename))

    for filename in relevant_files:
        if filename.endswith(".pb"):
            instance, profile = parse_pabulib(filename)
            meta = instance.meta or {}
            district = meta["subunit"] if "subunit" in meta else "citywide"
            instances[district] = instance
            profiles[district] = profile
    return instances, profiles
