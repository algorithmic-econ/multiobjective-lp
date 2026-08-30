from pathlib import Path

import pytest
from pabutools.election import Instance

from helpers.runners.model import Utility
from helpers.transformers.pabutools_utils import (
    detect_utility_from_instances,
    load_pabutools_by_district,
)

from .fixtures.pabutools_factories import make_instance, make_project

FIXTURE_INPUT = (
    Path(__file__).parent / "fixtures" / "input" / "krakow_2024_mini"
)


def _instance_with(**meta) -> Instance:
    instance = make_instance([make_project("p1", 100)], budget=100)
    instance.meta = {**(instance.meta or {}), **meta}
    return instance


@pytest.mark.parametrize(
    ("vote_type", "expected"),
    [
        ("approval", Utility.COST),
        ("ordinal", Utility.COST_ORDINAL),
        ("cumulative", Utility.COST_CUMULATIVE),
        ("choose-1", Utility.COST),
    ],
)
def test_detect_utility_maps_vote_type(vote_type, expected):
    instances = {"d1": _instance_with(vote_type=vote_type)}

    assert detect_utility_from_instances(instances) == expected


def test_detect_utility_agrees_across_districts():
    instances = {
        "d1": _instance_with(vote_type="ordinal"),
        "d2": _instance_with(vote_type="ordinal"),
    }

    assert detect_utility_from_instances(instances) == Utility.COST_ORDINAL


def test_detect_utility_missing_vote_type_raises():
    with pytest.raises(ValueError, match="missing vote_type"):
        detect_utility_from_instances({"d1": _instance_with()})


def test_detect_utility_inconsistent_vote_types_raises():
    instances = {
        "d1": _instance_with(vote_type="approval"),
        "d2": _instance_with(vote_type="ordinal"),
    }

    with pytest.raises(ValueError, match="Inconsistent vote_types"):
        detect_utility_from_instances(instances)


def test_detect_utility_unmapped_vote_type_raises():
    instances = {"d1": _instance_with(vote_type="score")}

    with pytest.raises(NotImplementedError, match="no utility mapping"):
        detect_utility_from_instances(instances)


def test_load_pabutools_by_district_reads_directory():
    instances, profiles = load_pabutools_by_district(str(FIXTURE_INPUT))

    # keyed by meta["subunit"], one entry per .pb file
    assert set(instances) == set(profiles)
    assert len(instances) == 2
    subunits = {
        (instance.meta or {}).get("subunit") for instance in instances.values()
    }
    assert subunits == set(instances)


def test_load_pabutools_by_district_reads_single_file():
    single = sorted(FIXTURE_INPUT.glob("*.pb"))[0]

    instances, profiles = load_pabutools_by_district(str(single))

    assert len(instances) == 1
    assert len(profiles) == 1


def test_load_pabutools_by_district_ignores_non_pb_files(tmp_path):
    (tmp_path / "notes.txt").write_text("not a pabulib file")

    assert load_pabutools_by_district(str(tmp_path)) == ({}, {})


def test_load_pabutools_by_district_ignores_non_pb_path(tmp_path):
    other = tmp_path / "notes.txt"
    other.write_text("not a pabulib file")

    assert load_pabutools_by_district(str(other)) == ({}, {})
