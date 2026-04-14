import pytest

from helpers.transformers.pabutoolsToMoLp import (
    compute_category_lb,
    compute_district_lb,
    compute_voter_category_shares,
)

from .fixtures.pabutools_factories import (
    make_approval_profile,
    make_instance,
    make_project,
)

# -- compute_district_lb --


def test_district_lb_basic():
    # budget=500, max_cost=300 → lb=200
    p1 = make_project("p1", 100, set())
    p2 = make_project("p2", 300, set())
    instance = make_instance([p1, p2], 500)

    assert compute_district_lb(instance) == 200


def test_district_lb_single_project():
    p1 = make_project("p1", 400, set())
    instance = make_instance([p1], 1000)

    assert compute_district_lb(instance) == 600


def test_district_lb_budget_equals_max():
    p1 = make_project("p1", 300, set())
    instance = make_instance([p1], 300)

    assert compute_district_lb(instance) == 0


def test_district_lb_empty_instance():
    instance = make_instance([], 500)

    # max defaults to 0, so lb = 500
    assert compute_district_lb(instance) == 500


# -- compute_voter_category_shares --


def test_shares_empty_profiles():
    p1 = make_project("p1", 100, {"edu"})
    instance = make_instance([p1], 1000)
    profile = make_approval_profile({}, {})

    result = compute_voter_category_shares(
        {"district": instance}, {"district": profile}, "APPROVAL", 1000, False
    )

    assert result == {}


def test_shares_single_voter_approval():
    # 1 voter, 2 projects in different cats, APPROVAL → equal weight
    p1 = make_project("p1", 100, {"edu"})
    p2 = make_project("p2", 200, {"env"})
    instance = make_instance([p1, p2], 1000)
    profile = make_approval_profile({"v1": ["p1", "p2"]}, {"p1": p1, "p2": p2})

    result = compute_voter_category_shares(
        {"district": instance}, {"district": profile}, "APPROVAL", 1000, False
    )

    # voter_budget=1000, weight 1 each, total_weight=2
    # edu: 1000*(1/2)=500, env: 1000*(1/2)=500
    assert result["edu"] == pytest.approx(500)
    assert result["env"] == pytest.approx(500)


def test_shares_cost_weighting():
    p1 = make_project("p1", 100, {"edu"})
    p2 = make_project("p2", 200, {"env"})
    instance = make_instance([p1, p2], 900)
    profile = make_approval_profile({"v1": ["p1", "p2"]}, {"p1": p1, "p2": p2})

    result = compute_voter_category_shares(
        {"district": instance}, {"district": profile}, "APPROVAL", 900, True
    )

    # use_cost=True → cost weights: 100, 200, total=300
    # edu: 900*(100/300)=300, env: 900*(200/300)=600
    assert result["edu"] == pytest.approx(300)
    assert result["env"] == pytest.approx(600)


def test_shares_multi_cat_project_splits():
    # project in both edu and env → share split evenly
    p1 = make_project("p1", 100, {"edu", "env"})
    instance = make_instance([p1], 1000)
    profile = make_approval_profile({"v1": ["p1"]}, {"p1": p1})

    result = compute_voter_category_shares(
        {"district": instance}, {"district": profile}, "APPROVAL", 10000, False
    )

    # single project, single voter, weight=1, voter_budget=1000
    # share=1000, split across 2 cats → 500 each
    assert result["edu"] == pytest.approx(500)
    assert result["env"] == pytest.approx(500)


def test_shares_two_voters_different_prefs():
    p1 = make_project("p1", 100, {"edu"})
    p2 = make_project("p2", 200, {"env"})
    instance = make_instance([p1, p2], 1000)
    profile = make_approval_profile(
        {"v1": ["p1"], "v2": ["p2"]}, {"p1": p1, "p2": p2}
    )

    result = compute_voter_category_shares(
        {"district": instance}, {"district": profile}, "APPROVAL", 1000, False
    )

    # 2 voters, voter_budget = 1000/2 = 500
    # v1 → all weight to edu: 500
    # v2 → all weight to env: 500
    assert result["edu"] == pytest.approx(500)
    assert result["env"] == pytest.approx(500)


# -- compute_category_lb --


def test_category_lb_single_voter():
    p1 = make_project("p1", 100, {"edu"})
    instance = make_instance([p1], 1000)
    profile = make_approval_profile({"v1": ["p1"]}, {"p1": p1})

    result = compute_category_lb(
        "edu",
        {"district": instance},
        {"district": profile},
        "APPROVAL",
        1000,
        False,
    )

    # share=1000, max_cost=100 → lb=900
    assert result == 900


def test_category_lb_two_cats():
    p1 = make_project("p1", 100, {"edu"})
    p2 = make_project("p2", 200, {"env"})
    instance = make_instance([p1, p2], 1000)
    profile = make_approval_profile({"v1": ["p1", "p2"]}, {"p1": p1, "p2": p2})

    result = compute_category_lb(
        "edu",
        {"district": instance},
        {"district": profile},
        "APPROVAL",
        1000,
        False,
    )

    # share_edu=500, max_edu_cost=100 → lb=400
    assert result == 400


def test_category_lb_use_cost():
    p1 = make_project("p1", 100, {"edu"})
    p2 = make_project("p2", 200, {"env"})
    instance = make_instance([p1, p2], 900)
    profile = make_approval_profile({"v1": ["p1", "p2"]}, {"p1": p1, "p2": p2})

    result = compute_category_lb(
        "edu",
        {"district": instance},
        {"district": profile},
        "APPROVAL",
        900,
        True,
    )

    # cost weights: 100/300 → share_edu = 900*(100/300)=300
    # lb = int(300) - 100 = 200
    assert result == 200


def test_category_lb_missing_category():
    p1 = make_project("p1", 100, {"edu"})
    instance = make_instance([p1], 1000)
    profile = make_approval_profile({"v1": ["p1"]}, {"p1": p1})

    result = compute_category_lb(
        "sports",
        {"district": instance},
        {"district": profile},
        "APPROVAL",
        1000,
        False,
    )

    # no projects in sports → share=0, max_cost=0 → lb=0
    assert result == 0
