import pytest
from pulp import LpConstraintGE, LpConstraintLE

from helpers.transformers.pabutoolsConstants import CONSTRAINT_PREFIX
from helpers.transformers.pabutoolsToMoLp import (
    create_baseline_constraints,
    create_category_constraint,
    create_constraints_from_config,
    create_district_constraint,
)

from .fixtures.pabutools_factories import (
    make_approval_profile,
    make_cumulative_profile,
    make_ordinal_profile,
)

# -- create_baseline_constraints --


def test_baseline_single_district_returns_one_constraint(
    single_district_setup,
):
    instances, _, _, variables = single_district_setup

    result = create_baseline_constraints(instances, variables)

    assert len(result) == 1
    assert result[0].sense == LpConstraintLE


def test_baseline_single_district_rhs(single_district_setup):
    instances, _, _, variables = single_district_setup

    result = create_baseline_constraints(instances, variables)

    # rhs stored as -constant
    assert -result[0].constant == 500


def test_baseline_multi_district_returns_n_plus_1(multi_district_setup):
    instances, _, _, variables = multi_district_setup

    result = create_baseline_constraints(instances, variables)

    # 2 per-district + 1 total = 3
    assert len(result) == 3


def test_baseline_multi_district_all_LE(multi_district_setup):
    instances, _, _, variables = multi_district_setup

    result = create_baseline_constraints(instances, variables)

    for c in result:
        assert c.sense == LpConstraintLE


def test_baseline_multi_district_total_budget(multi_district_setup):
    instances, _, _, variables = multi_district_setup

    result = create_baseline_constraints(instances, variables)

    total_constraint = [c for c in result if "total_budget" in c.name][0]
    assert -total_constraint.constant == 500  # 300 + 200


def test_baseline_coefficients(single_district_setup):
    instances, _, by_name, variables = single_district_setup

    result = create_baseline_constraints(instances, variables)
    constraint = result[0]

    # coefficient for each variable matches project cost
    for var_name, var in variables.items():
        coef = constraint[var]
        expected_cost = int(by_name[var_name].cost)
        assert coef == expected_cost


# -- create_category_constraint --


def test_category_upper_ratio(single_district_setup):
    instances, profiles, by_name, variables = single_district_setup
    projects = list(by_name.values())
    config = {
        "key": "CATEGORY",
        "value": "edu",
        "bound": "UPPER",
        "budget_ratio": 0.5,
    }

    result = create_category_constraint(
        config, variables, projects, 500, instances, profiles, "APPROVAL"
    )

    assert result.sense == LpConstraintLE
    assert -result.constant == 250  # 0.5 * 500


def test_category_lower_ratio(single_district_setup):
    instances, profiles, by_name, variables = single_district_setup
    projects = list(by_name.values())
    config = {
        "key": "CATEGORY",
        "value": "edu",
        "bound": "LOWER",
        "budget_ratio": 0.3,
    }

    result = create_category_constraint(
        config, variables, projects, 1000, instances, profiles, "APPROVAL"
    )

    assert result.sense == LpConstraintGE
    assert -result.constant == 300


@pytest.mark.parametrize(
    "utility, profile_factory, ballots, expected_lb",
    [
        pytest.param(
            "APPROVAL",
            make_approval_profile,
            {"v1": ["p1", "p2"], "v2": ["p2", "p3"]},
            -113,
            id="approval: w=1 each → edu_share=187.5",
        ),
        pytest.param(
            "ORDINAL",
            make_ordinal_profile,
            {"v1": ["p1", "p2"], "v2": ["p2", "p3"]},
            -92,
            id="ordinal: w=[2,1] by rank → edu_share=208.3",
        ),
        pytest.param(
            "CUMULATIVE",
            make_cumulative_profile,
            {"v1": {"p1": 3, "p2": 2}, "v2": {"p2": 1, "p3": 4}},
            -50,
            id="cumulative: w=points → edu_share=250",
        ),
    ],
)
def test_category_strategy_vote_share(
    single_district_setup, utility, profile_factory, ballots, expected_lb
):
    """vote_share: voter_budget (250/voter) split by weight/total_weight.
    Multi-cat projects split share across categories.
    LB = int(edu_share) - max_cost_in_category(300).
    Negative LB ⇒ trivially satisfied."""
    instances, _, by_name, variables = single_district_setup
    projects = list(by_name.values())
    profiles = {"d1": profile_factory(ballots, by_name)}
    config = {
        "key": "CATEGORY",
        "value": "edu",
        "bound": "LOWER",
        "strategy": "category_vote_share",
    }

    result = create_category_constraint(
        config, variables, projects, 500, instances, profiles, utility
    )

    assert result.sense == LpConstraintGE
    assert -result.constant == expected_lb
    var_names = {v.name for v in result.keys()}
    assert variables["p1"].name in var_names
    assert variables["p2"].name not in var_names
    assert result[variables["p1"]] == 100
    assert result[variables["p3"]] == 300


@pytest.mark.parametrize(
    "utility, profile_factory, ballots",
    [
        pytest.param(
            "APPROVAL",
            make_approval_profile,
            {"v1": ["p1", "p2"], "v2": ["p2", "p3"]},
            id="approval",
        ),
        pytest.param(
            "ORDINAL",
            make_ordinal_profile,
            {"v1": ["p1", "p2"], "v2": ["p2", "p3"]},
            id="ordinal",
        ),
        pytest.param(
            "CUMULATIVE",
            make_cumulative_profile,
            {"v1": {"p1": 3, "p2": 2}, "v2": {"p2": 1, "p3": 4}},
            id="cumulative",
        ),
    ],
)
def test_category_strategy_cost_share(
    single_district_setup, utility, profile_factory, ballots
):
    """cost_share: voter_budget split by project_cost/total_cost.
    Utility-independent — same projects in ballot → same LB for all profiles.
    edu_share = 83.33 (v1→p1) + 75 (v2→p3/2) = 158.33.
    LB = int(158.33) - 300 = -142."""
    instances, _, by_name, variables = single_district_setup
    projects = list(by_name.values())
    profiles = {"d1": profile_factory(ballots, by_name)}
    config = {
        "key": "CATEGORY",
        "value": "edu",
        "bound": "LOWER",
        "strategy": "category_cost_share",
    }

    result = create_category_constraint(
        config, variables, projects, 500, instances, profiles, utility
    )

    assert result.sense == LpConstraintGE
    assert -result.constant == -142
    var_names = {v.name for v in result.keys()}
    assert variables["p1"].name in var_names
    assert variables["p3"].name in var_names
    assert variables["p2"].name not in var_names
    assert result[variables["p1"]] == 100
    assert result[variables["p3"]] == 300


def test_category_only_matching_projects(single_district_setup):
    instances, profiles, by_name, variables = single_district_setup
    projects = list(by_name.values())
    config = {
        "key": "CATEGORY",
        "value": "edu",
        "bound": "UPPER",
        "budget_ratio": 1.0,
    }

    result = create_category_constraint(
        config, variables, projects, 500, instances, profiles, "APPROVAL"
    )

    # p2 (env only) should not appear in constraint
    # p1 (edu) and p3 (edu+env) should
    var_names_in_constraint = {v.name for v in result.keys()}
    assert variables["p2"].name not in var_names_in_constraint
    assert variables["p1"].name in var_names_in_constraint
    assert variables["p3"].name in var_names_in_constraint


def test_category_constraint_name_prefix(single_district_setup):
    instances, profiles, by_name, variables = single_district_setup
    projects = list(by_name.values())

    ub_config = {
        "key": "CATEGORY",
        "value": "edu",
        "bound": "UPPER",
        "budget_ratio": 0.5,
    }
    lb_config = {
        "key": "CATEGORY",
        "value": "edu",
        "bound": "LOWER",
        "budget_ratio": 0.3,
    }

    ub = create_category_constraint(
        ub_config, variables, projects, 500, instances, profiles, "APPROVAL"
    )
    lb = create_category_constraint(
        lb_config, variables, projects, 500, instances, profiles, "APPROVAL"
    )

    assert ub.name.startswith(f"{CONSTRAINT_PREFIX}_ub_")
    assert lb.name.startswith(f"{CONSTRAINT_PREFIX}_lb_")


# -- create_district_constraint --


def test_district_upper_ratio(multi_district_setup):
    instances, _, by_name, variables = multi_district_setup
    d1_projects = list(instances["d1"])
    config = {
        "key": "DISTRICT",
        "value": "d1",
        "bound": "UPPER",
        "budget_ratio": 0.6,
    }

    result = create_district_constraint(
        config, variables, d1_projects, 500, instances["d1"]
    )

    assert result.sense == LpConstraintLE
    assert -result.constant == 300  # 0.6 * 500


def test_district_lower_ratio(multi_district_setup):
    instances, _, by_name, variables = multi_district_setup
    d1_projects = list(instances["d1"])
    config = {
        "key": "DISTRICT",
        "value": "d1",
        "bound": "LOWER",
        "budget_ratio": 0.2,
    }

    result = create_district_constraint(
        config, variables, d1_projects, 500, instances["d1"]
    )

    assert result.sense == LpConstraintGE
    assert -result.constant == 100  # 0.2 * 500


def test_district_strategy_budget_minus_max(multi_district_setup):
    instances, _, by_name, variables = multi_district_setup
    d1_projects = list(instances["d1"])
    config = {
        "key": "DISTRICT",
        "value": "d1",
        "bound": "LOWER",
        "strategy": "district_budget_minus_max",
    }

    result = create_district_constraint(
        config, variables, d1_projects, 500, instances["d1"]
    )

    assert result.sense == LpConstraintGE
    # d1 budget=300, max cost=200 → lb=100
    assert -result.constant == 100


def test_district_only_includes_district_projects(multi_district_setup):
    instances, _, by_name, variables = multi_district_setup
    d1_projects = list(instances["d1"])
    config = {
        "key": "DISTRICT",
        "value": "d1",
        "bound": "UPPER",
        "budget_ratio": 1.0,
    }

    result = create_district_constraint(
        config, variables, d1_projects, 500, instances["d1"]
    )

    # d2 projects should not appear in constraint
    var_names_in_constraint = {v.name for v in result.keys()}
    assert variables["p3"].name not in var_names_in_constraint
    assert variables["p4"].name not in var_names_in_constraint


# -- create_constraints_from_config --


def test_config_empty(single_district_setup):
    instances, profiles, _, variables = single_district_setup

    result = create_constraints_from_config(
        [], instances, profiles, variables, "APPROVAL"
    )

    assert result == []


def test_config_single_category(single_district_setup):
    instances, profiles, _, variables = single_district_setup
    configs = [
        {
            "key": "CATEGORY",
            "value": "edu",
            "bound": "UPPER",
            "budget_ratio": 0.5,
        }
    ]

    result = create_constraints_from_config(
        configs, instances, profiles, variables, "APPROVAL"
    )

    assert len(result) == 1


def test_config_single_district(multi_district_setup):
    instances, profiles, _, variables = multi_district_setup
    configs = [
        {
            "key": "DISTRICT",
            "value": "d1",
            "bound": "LOWER",
            "budget_ratio": 0.2,
        }
    ]

    result = create_constraints_from_config(
        configs, instances, profiles, variables, "APPROVAL"
    )

    assert len(result) == 1


def test_config_wildcard_category(single_district_setup):
    instances, profiles, _, variables = single_district_setup
    configs = [
        {
            "key": "CATEGORY",
            "value": "*",
            "bound": "UPPER",
            "budget_ratio": 0.8,
        }
    ]

    result = create_constraints_from_config(
        configs, instances, profiles, variables, "APPROVAL"
    )

    # 2 categories: edu, env
    assert len(result) == 2


def test_config_wildcard_district(multi_district_setup):
    instances, profiles, _, variables = multi_district_setup
    configs = [
        {
            "key": "DISTRICT",
            "value": "*",
            "bound": "LOWER",
            "budget_ratio": 0.1,
        }
    ]

    result = create_constraints_from_config(
        configs, instances, profiles, variables, "APPROVAL"
    )

    # 2 districts
    assert len(result) == 2


def test_config_unknown_category_skipped(single_district_setup):
    instances, profiles, _, variables = single_district_setup
    configs = [
        {
            "key": "CATEGORY",
            "value": "nonexistent",
            "bound": "UPPER",
            "budget_ratio": 0.5,
        }
    ]

    result = create_constraints_from_config(
        configs, instances, profiles, variables, "APPROVAL"
    )

    assert len(result) == 0


def test_config_unknown_district_skipped(multi_district_setup):
    instances, profiles, _, variables = multi_district_setup
    configs = [
        {
            "key": "DISTRICT",
            "value": "nonexistent",
            "bound": "LOWER",
            "budget_ratio": 0.1,
        }
    ]

    result = create_constraints_from_config(
        configs, instances, profiles, variables, "APPROVAL"
    )

    assert len(result) == 0


def test_config_mixed(multi_district_setup):
    instances, profiles, _, variables = multi_district_setup
    configs = [
        {
            "key": "CATEGORY",
            "value": "edu",
            "bound": "UPPER",
            "budget_ratio": 0.5,
        },
        {
            "key": "DISTRICT",
            "value": "d1",
            "bound": "LOWER",
            "budget_ratio": 0.1,
        },
    ]

    result = create_constraints_from_config(
        configs, instances, profiles, variables, "APPROVAL"
    )

    assert len(result) == 2
