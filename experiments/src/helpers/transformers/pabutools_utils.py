from typing import TypeAlias
from pathlib import Path
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

    source = Path(path)
    relevant_files: list[Path] = []
    if source.is_file() and source.suffix == ".pb":
        relevant_files.append(source)

    if source.is_dir():
        # sorted by name: iterdir order is fs-dependent; district order defines
        # LP var order -> solver tie-breaks -> nondeterministic `selected`
        for file in sorted(source.iterdir(), key=lambda f: f.name):
            if file.suffix == ".pb":
                relevant_files.append(file)

    for file in relevant_files:
        instance, profile = parse_pabulib(str(file))
        meta = instance.meta or {}
        district = meta["subunit"] if "subunit" in meta else "citywide"
        instances[district] = instance
        profiles[district] = profile
    return instances, profiles
