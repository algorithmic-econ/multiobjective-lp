"""Native (C++) metrics vs their python counterparts (oracle).

Generic over `PYTHON_COUNTERPART`: registering a new native metric there
(see helpers/analyzers/native_metrics.py) puts it under every parity test
below. Exact `==` everywhere: C++ mirrors pulp's summation order, so doubles
are bit-identical.
"""

import sys

import pytest
from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from muoblp.utils.lp_reader_utils import read_lp_file
from pulp import LpAffineExpression, LpVariable, PulpSolverError

from analyzer_runner import analyze_runner_result
from helpers.analyzers import native_metrics
from helpers.analyzers.metrics import (
    ejr_plus,
    exclusion_ratio,
    get_metric_strategy,
    get_metrics,
)
from helpers.analyzers.model import AnalyzerFailure, AnalyzerResult, Metric
from helpers.analyzers.native_metrics import (
    NATIVE_STRATEGIES,
    PYTHON_COUNTERPART,
    build_solved_instance,
    ejr_plus_native,
    exclusion_ratio_native,
)
from helpers.runners.model import RunnerResult, Solver, Source, Utility
from helpers.utils.enhance_from_solver_result import (
    enhance_problem_from_solver_result,
)
from helpers.utils.utils import write_to_json

from .fixtures.problem_factories import (
    HANDCRAFTED_FACTORIES,
    make_all_excluded_problem,
    make_ejr_violation_problem,
    make_float_constant_problem,
    make_multi_constraint_problem,
    make_none_excluded_problem,
    make_objective_only_variable_problem,
    make_random_problem,
    make_tiny_problem,
    make_weighted_objectives_problem,
)
from .fixtures.runner_result_factories import (
    cache_key_fields,
)

PAIRS = list(PYTHON_COUNTERPART.items())
PAIR_IDS = [native.value for native, _ in PAIRS]
RANDOM_SEEDS = range(200)

# exclusion_ratio of each handcrafted factory (computed by hand, see the
# factory docstrings); keeps parity from passing with both impls wrong
EXPECTED_EXCLUSION_RATIO = {
    make_tiny_problem: 0.0,
    make_ejr_violation_problem: 0.5,
    make_all_excluded_problem: 1.0,
    make_none_excluded_problem: 0.0,
    make_objective_only_variable_problem: 0.5,
    make_multi_constraint_problem: 0.5,
    make_weighted_objectives_problem: 1 / 3,
    make_float_constant_problem: 0.4,
}

# ejr_plus (up_to_one) of each handcrafted factory, by hand: (k / n) * B
# - cost vs satisfaction of k-th approver (ascending) of unelected projects
EXPECTED_EJR_PLUS = {
    make_tiny_problem: 0,
    make_ejr_violation_problem: 1,  # p2: 0 < 250/4 - 10
    make_all_excluded_problem: 1,  # p1, k=2: 0 < 2/3 * 250 - 100
    make_none_excluded_problem: 1,  # p3, k=2: 30 < 2/3 * 100 - 30
    make_objective_only_variable_problem: 0,
    make_multi_constraint_problem: 0,
    make_weighted_objectives_problem: 0,
    make_float_constant_problem: 0,  # all selected
}


def _runner_result(problem_path, selected: list[str]) -> RunnerResult:
    return RunnerResult(
        **cache_key_fields(),
        time=0.1,
        solver=Solver.GREEDY,
        solver_options={},
        source_type=Source.PABUTOOLS,
        utility_type=Utility.COST,
        source_path="krakow_2024",
        constraints_configs=[],
        deduplicate_objectives=False,
        problem_path=str(problem_path),
        instance_size=len(selected),
        selected=selected,
    )


def _persist_happy_meta(tmp_path):
    # same shape analyze_runner_result gets from experiment_runner
    problem_path = tmp_path / "problem_ok.lp"
    meta_path = tmp_path / "meta_ok.json"
    make_multi_constraint_problem().write_lp(str(problem_path))
    result = _runner_result(problem_path, ["p1", "p3"])
    write_to_json(meta_path, result.model_dump(mode="json", exclude_none=True))
    return meta_path


def _block_bindings(monkeypatch, module: str) -> None:
    # None in sys.modules -> import raises. An already-imported submodule
    # entry short-circuits the parent check, so evict it for the parent case.
    if module == "muoblpbindings":
        monkeypatch.delitem(
            sys.modules, "muoblpbindings.metrics", raising=False
        )
    monkeypatch.setitem(sys.modules, module, None)


def _variable(problem: MultiObjectiveLpProblem, name: str) -> LpVariable:
    return next(v for v in problem.variables() if v.name == name)


# --- parity -----------------------------------------------------------


@pytest.mark.parametrize(("native", "python"), PAIRS, ids=PAIR_IDS)
@pytest.mark.parametrize(
    "factory", HANDCRAFTED_FACTORIES, ids=lambda f: f.__name__
)
def test_parity_handcrafted(native, python, factory):
    result = get_metrics([python, native], factory())
    assert result[native] == result[python]


def test_handcrafted_absolute_values():
    assert set(EXPECTED_EXCLUSION_RATIO) == set(HANDCRAFTED_FACTORIES)
    for factory, expected in EXPECTED_EXCLUSION_RATIO.items():
        result = get_metrics(
            [Metric.EXCLUSION_RATIO, Metric.EXCLUSION_RATIO_NATIVE],
            factory(),
        )
        assert result[Metric.EXCLUSION_RATIO] == {"exclusion_ratio": expected}
        assert result[Metric.EXCLUSION_RATIO_NATIVE] == {
            "exclusion_ratio": expected
        }, factory.__name__


def test_handcrafted_ejr_plus_absolute_values():
    assert set(EXPECTED_EJR_PLUS) == set(HANDCRAFTED_FACTORIES)
    for factory, expected in EXPECTED_EJR_PLUS.items():
        result = get_metrics(
            [Metric.EJR_PLUS, Metric.EJR_PLUS_NATIVE], factory()
        )
        assert result[Metric.EJR_PLUS] == {"ejr_plus": expected}
        assert result[Metric.EJR_PLUS_NATIVE] == {"ejr_plus": expected}, (
            factory.__name__
        )


@pytest.mark.parametrize(("native", "python"), PAIRS, ids=PAIR_IDS)
def test_parity_random(native, python):
    for seed in RANDOM_SEEDS:
        result = get_metrics([python, native], make_random_problem(seed))
        assert result[native] == result[python], f"seed {seed}"


def test_random_generator_is_not_degenerate():
    ratios = {
        exclusion_ratio(make_random_problem(seed))["exclusion_ratio"]
        for seed in RANDOM_SEEDS
    }
    assert len(ratios) >= 3
    assert 0.0 in ratios and 1.0 in ratios

    violations = {
        ejr_plus(make_random_problem(seed))["ejr_plus"]
        for seed in RANDOM_SEEDS
    }
    assert 0 in violations and len(violations) >= 3


def test_random_generator_is_deterministic():
    def snapshot(problem):
        return (
            [{v.name: c for v, c in o.items()} for o in problem.objectives],
            {v.name: v.varValue for v in problem.variables()},
        )

    assert snapshot(make_random_problem(7)) == snapshot(make_random_problem(7))
    assert snapshot(make_random_problem(7)) != snapshot(make_random_problem(8))


@pytest.mark.parametrize(("native", "python"), PAIRS, ids=PAIR_IDS)
@pytest.mark.parametrize(
    ("factory", "selected"),
    [
        (make_tiny_problem, ["p1"]),
        (make_ejr_violation_problem, ["p2"]),
        (make_multi_constraint_problem, ["p2", "p3", "p4"]),
        (make_weighted_objectives_problem, ["p1"]),
    ],
    ids=lambda x: x.__name__ if callable(x) else None,
)
def test_parity_lp_roundtrip(tmp_path, native, python, factory, selected):
    # mirrors analyze_runner_result: read_lp_file -> enhance -> metrics.
    # Factories are roundtrip-safe (positive int coefs, no empty voters,
    # no objective-only variables).
    path = tmp_path / "problem.lp"
    factory().write_lp(str(path))
    problem = read_lp_file(str(path))
    problem = enhance_problem_from_solver_result(
        _runner_result(path, selected), problem
    )

    result = get_metrics([python, native], problem)

    assert result[native] == result[python]
    # proper subset selected -> restored values are really applied
    all_names = {v.name for v in problem.variables()}
    assert 0 < len(selected) < len(all_names)


def test_roundtrip_absolute_value(tmp_path):
    # multi-constraint, select p2,p3,p4: v1=0 (p1), v2=10, v3=5+5, v4=8,
    # v5=0 (p1,p5), v6=0 (p5) -> 3 of 6 excluded
    path = tmp_path / "problem.lp"
    make_multi_constraint_problem().write_lp(str(path))
    problem = enhance_problem_from_solver_result(
        _runner_result(path, ["p2", "p3", "p4"]), read_lp_file(str(path))
    )
    result = get_metrics(
        [Metric.EXCLUSION_RATIO, Metric.EXCLUSION_RATIO_NATIVE], problem
    )
    assert result[Metric.EXCLUSION_RATIO] == {"exclusion_ratio": 0.5}
    assert result[Metric.EXCLUSION_RATIO_NATIVE] == {"exclusion_ratio": 0.5}


# --- handle semantics -------------------------------------------------


@pytest.mark.parametrize(("native", "python"), PAIRS, ids=PAIR_IDS)
def test_handle_reuse_gives_same_result(native, python):
    problem = make_multi_constraint_problem()
    handle = build_solved_instance(problem)
    strategy = NATIVE_STRATEGIES[native]

    assert strategy(handle) == strategy(handle)
    assert strategy(handle) == get_metrics([python], problem)[python]


@pytest.mark.parametrize(("native", "python"), PAIRS, ids=PAIR_IDS)
def test_handle_is_snapshot(native, python):
    problem = make_tiny_problem()
    strategy = NATIVE_STRATEGIES[native]
    handle = build_solved_instance(problem)
    before = strategy(handle)

    _variable(problem, "p1").setInitialValue(0)  # mutate after build

    assert strategy(handle) == before
    fresh = strategy(build_solved_instance(problem))
    assert fresh == get_metrics([python], problem)[python]


def test_snapshot_exclusion_ratio_values():
    # p1 = 1: v1 = v2 = 100 -> 0.0. After p1 = 0: v1 = v2 = 0 -> 1.0
    problem = make_tiny_problem()
    handle = build_solved_instance(problem)
    _variable(problem, "p1").setInitialValue(0)

    assert exclusion_ratio_native(handle) == {"exclusion_ratio": 0.0}
    fresh = build_solved_instance(problem)
    assert exclusion_ratio_native(fresh) == {"exclusion_ratio": 1.0}


def test_handle_counts():
    handle = build_solved_instance(make_tiny_problem())
    assert (handle.num_voters, handle.num_candidates) == (2, 2)

    # p3, p4 are in objectives only: still counted
    problem = make_objective_only_variable_problem()
    assert {v.name for v in problem.variables()} == {"p1", "p2"}
    handle = build_solved_instance(problem)
    assert (handle.num_voters, handle.num_candidates) == (4, 4)


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_handle_counts_random(seed):
    problem = make_random_problem(seed)
    handle = build_solved_instance(problem)
    assert handle.num_voters == len(problem.objectives)
    assert handle.num_candidates == len(problem.variables())


# --- errors -----------------------------------------------------------


def test_empty_objectives_error_types():
    problem = MultiObjectiveLpProblem("empty", objectives=[])
    p1 = LpVariable("p1", cat="Binary")
    p1.setInitialValue(1)
    problem += 10 * p1 <= 20, "pb_constraint"

    with pytest.raises(ZeroDivisionError):
        get_metrics([Metric.EXCLUSION_RATIO], problem)
    with pytest.raises(ValueError):
        get_metrics([Metric.EXCLUSION_RATIO_NATIVE], problem)


def test_ejr_plus_threshold_is_not_fused():
    # (1 / 5) * 215 - 43 is 0.0 in python, 2.4e-15 with a fused
    # multiply-add -> a sat 0 approver would fail only natively
    p1 = LpVariable("p1", cat="Binary")
    p2 = LpVariable("p2", cat="Binary")
    p1.setInitialValue(0)
    p2.setInitialValue(0)
    objectives = [LpAffineExpression({p1: 5})] + [
        LpAffineExpression({p2: 1}) for _ in range(4)
    ]
    problem = MultiObjectiveLpProblem(
        "fma", objectives=objectives, objectives_weights={}
    )
    problem += 43 * p1 + 500 * p2 <= 215, "pb_constraint"

    result = get_metrics([Metric.EJR_PLUS, Metric.EJR_PLUS_NATIVE], problem)
    assert result[Metric.EJR_PLUS] == {"ejr_plus": 0}
    assert result[Metric.EJR_PLUS_NATIVE] == {"ejr_plus": 0}


def test_ejr_plus_up_to_one_false():
    from muoblpbindings.metrics import ejr_plus as native_ejr_plus

    # all_excluded, no cost slack: p1 and p2 fail at k=1 (0 < 250/3)
    handle = build_solved_instance(make_all_excluded_problem())
    assert native_ejr_plus(handle, up_to_one=False) == 2
    assert native_ejr_plus(handle) == 1
    assert ejr_plus_native(handle) == {"ejr_plus": 1}


def test_ejr_plus_empty_objectives():
    problem = MultiObjectiveLpProblem("empty", objectives=[])
    p1 = LpVariable("p1", cat="Binary")
    p1.setInitialValue(0)
    problem += 10 * p1 <= 20, "pb_constraint"

    result = get_metrics([Metric.EJR_PLUS, Metric.EJR_PLUS_NATIVE], problem)
    assert result[Metric.EJR_PLUS] == {"ejr_plus": 0}
    assert result[Metric.EJR_PLUS_NATIVE] == {"ejr_plus": 0}


def test_ejr_plus_without_pb_constraint():
    # no LE constraint covers all candidates (GE one does not count)
    problem = make_tiny_problem()
    p1, p2 = _variable(problem, "p1"), _variable(problem, "p2")
    problem = MultiObjectiveLpProblem(
        "no_pb", objectives=problem.objectives, objectives_weights={}
    )
    problem += 100 * p1 <= 250, "district_a"
    problem += 200 * p2 <= 250, "district_b"
    problem += 100 * p1 + 200 * p2 >= 50, "lower"

    with pytest.raises(PulpSolverError, match="does not have"):
        get_metrics([Metric.EJR_PLUS], problem)
    with pytest.raises(ValueError, match="does not have"):
        get_metrics([Metric.EJR_PLUS_NATIVE], problem)
    # budget is only needed by ejr_plus: same handle serves exclusion ratio
    assert get_metrics([Metric.EXCLUSION_RATIO_NATIVE], problem) == {
        Metric.EXCLUSION_RATIO_NATIVE: {"exclusion_ratio": 0.0}
    }


def test_ejr_plus_too_many_pb_constraints():
    problem = make_tiny_problem()
    p1, p2 = _variable(problem, "p1"), _variable(problem, "p2")
    problem += 100 * p1 + 200 * p2 <= 300, "pb_constraint_2"

    with pytest.raises(PulpSolverError, match="too many"):
        get_metrics([Metric.EJR_PLUS], problem)
    with pytest.raises(ValueError, match="too many"):
        get_metrics([Metric.EJR_PLUS_NATIVE], problem)


def test_variable_without_value_is_rejected():
    # documented divergence: python counts such a voter as non-excluded
    # (None == 0 is False), native refuses the whole problem. Unreachable
    # in the analyzer flow (enhance sets every variable).
    problem = make_tiny_problem()
    p3 = LpVariable("p3", cat="Binary")  # varValue None
    problem += 10 * p3 <= 20, "extra"

    with pytest.raises(ValueError):
        build_solved_instance(problem)
    assert exclusion_ratio(problem) == {"exclusion_ratio": 0.0}


# --- fail loudly ------------------------------------------------------


@pytest.mark.parametrize(
    "module", ["muoblpbindings", "muoblpbindings.metrics"]
)
def test_missing_bindings_raise_import_error(monkeypatch, module):
    _block_bindings(monkeypatch, module)
    problem = make_tiny_problem()

    with pytest.raises(ImportError):
        get_metrics([Metric.EXCLUSION_RATIO_NATIVE], problem)
    # python-only metrics are unaffected
    assert get_metrics(
        [Metric.EXCLUSION_RATIO, Metric.INSTANCE_SIZE, Metric.TOTAL_COST],
        problem,
    ) == {
        Metric.EXCLUSION_RATIO: {"exclusion_ratio": 0.0},
        Metric.INSTANCE_SIZE: {"size": 2},
        Metric.TOTAL_COST: {"total_cost": 100},
    }


@pytest.mark.parametrize(
    "module", ["muoblpbindings", "muoblpbindings.metrics"]
)
def test_missing_bindings_give_analyzer_failure(tmp_path, monkeypatch, module):
    meta_path = _persist_happy_meta(tmp_path)
    _block_bindings(monkeypatch, module)

    result = analyze_runner_result(meta_path, [Metric.EXCLUSION_RATIO_NATIVE])

    assert isinstance(result, AnalyzerFailure)
    assert result.error_type in ("ImportError", "ModuleNotFoundError")


def test_analyze_runner_result_populates_native_metric(tmp_path):
    meta_path = _persist_happy_meta(tmp_path)

    result = analyze_runner_result(
        meta_path, [Metric.EXCLUSION_RATIO, Metric.EXCLUSION_RATIO_NATIVE]
    )

    # selected p1, p3 -> v2, v4, v6 excluded
    assert isinstance(result, AnalyzerResult)
    assert result.EXCLUSION_RATIO_NATIVE == {"exclusion_ratio": 0.5}
    assert result.EXCLUSION_RATIO_NATIVE == result.EXCLUSION_RATIO


# --- registry ---------------------------------------------------------


def test_registries_are_consistent():
    assert set(NATIVE_STRATEGIES) == set(PYTHON_COUNTERPART)
    for native, python in PYTHON_COUNTERPART.items():
        assert native in AnalyzerResult.model_fields
        assert python in AnalyzerResult.model_fields
        assert python not in NATIVE_STRATEGIES
        get_metric_strategy(python)  # python oracle: must not raise
        with pytest.raises(NotImplementedError):
            get_metric_strategy(native)  # native has no python strategy
    assert native_metrics.NATIVE_STRATEGIES is NATIVE_STRATEGIES
