from helpers.transformers.pabutoolsToMoLp import (
    pabutools_to_multi_objective_lp,
)


def test_variable_count(single_district_setup):
    instances, profiles, _, _ = single_district_setup

    problem = pabutools_to_multi_objective_lp(
        instances, profiles, [], "APPROVAL"
    )

    assert len(problem.variables()) == 3


def test_objective_count(single_district_setup):
    instances, profiles, _, _ = single_district_setup

    problem = pabutools_to_multi_objective_lp(
        instances, profiles, [], "APPROVAL"
    )

    # 2 voters → 2 objectives
    assert len(problem.objectives) == 2


def test_baseline_constraint_present(single_district_setup):
    instances, profiles, _, _ = single_district_setup

    problem = pabutools_to_multi_objective_lp(
        instances, profiles, [], "APPROVAL"
    )

    constraint_names = list(problem.constraints.keys())
    budget_constraints = [n for n in constraint_names if "total_budget" in n]
    assert len(budget_constraints) == 1


def test_additional_constraints_from_config(single_district_setup):
    instances, profiles, _, _ = single_district_setup
    configs = [
        {
            "key": "CATEGORY",
            "value": "edu",
            "bound": "UPPER",
            "budget_ratio": 0.5,
        }
    ]

    problem = pabutools_to_multi_objective_lp(
        instances, profiles, configs, "APPROVAL"
    )

    constraint_names = list(problem.constraints.keys())
    # 1 baseline + 1 additional
    assert len(constraint_names) == 2


def test_multi_district_constraints(multi_district_setup):
    instances, profiles, _, _ = multi_district_setup

    problem = pabutools_to_multi_objective_lp(
        instances, profiles, [], "APPROVAL"
    )

    constraint_names = list(problem.constraints.keys())
    # 2 per-district + 1 total = 3
    assert len(constraint_names) == 3
