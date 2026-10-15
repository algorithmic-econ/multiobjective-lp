"""E2E parity: native metrics == python counterparts over a real pipeline.

Runs experiment_runner -> analyzer_runner on the tiny krakow fixture
(3 solvers x 2 utilities = 6 results) requesting every python counterpart
and every native metric, then compares them row by row, exactly.

To cover a new native metric: register it in `PYTHON_COUNTERPART`
(helpers/analyzers/native_metrics.py); METRICS below is derived from it.
"""

import json
from pathlib import Path

import pytest

from helpers.analyzers.native_metrics import PYTHON_COUNTERPART

pytestmark = pytest.mark.e2e

FIXTURE = Path(__file__).parent / "fixtures" / "input" / "krakow_2024_mini"
SOLVERS = ["GREEDY", "MES_UTILS", "MES_ADD1"]
UTILITIES = ["COST_ORDINAL", "APPROVAL"]
METRICS = [
    *(python.value for python in PYTHON_COUNTERPART.values()),
    *(native.value for native in PYTHON_COUNTERPART),
]


def test_e2e_native_parity(tmp_path):
    import analyzer_runner
    import experiment_runner

    results_path = f"{tmp_path}/results/"
    analysis_path = f"{tmp_path}/analysis/"

    experiment = {
        "concurrency": 1,
        "experiment_results_base_path": results_path,
        "runner_configs": [
            {
                "solver_type": solver,
                "solver_options": {},
                "source_type": "PABUTOOLS",
                "utility_type": utility,
                "source_directory_path": str(FIXTURE),
                "constraints_configs": [],
            }
            for solver in SOLVERS
            for utility in UTILITIES
        ],
    }
    experiment_runner.main(experiment)

    analyzer = {
        "analyzer_result_path": analysis_path,
        "experiment_results_base_path": results_path,
        "metrics": METRICS,
    }
    assert analyzer_runner.main(analyzer) == (6, 0)

    rows = json.loads(
        (Path(analysis_path) / "metrics-results.json").read_text()
    )
    assert len(rows) == 6
    assert not any("error_type" in row for row in rows)

    for row in rows:
        for native, python in PYTHON_COUNTERPART.items():
            label = f"{row['solver']}/{row['utility']}/{native.value}"
            # JSON round-trip of identical doubles is identical
            assert row[native.value] == row[python.value], label

    # parity on all-zero ratios would be a weak signal
    assert any(
        row[python.value]["exclusion_ratio"] > 0
        for row in rows
        for python in PYTHON_COUNTERPART.values()
    )
