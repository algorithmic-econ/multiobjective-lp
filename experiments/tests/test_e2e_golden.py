"""E2E golden test: runner -> analyzer over tiny 2-district fixture (T02).

Guards the whole pipeline (pabulib parse -> transform -> solve -> persist ->
analyze) before refactors. Goldens + normalization: see golden_utils.py and
tests/fixtures/README.md (incl. regen + manual mutation-check procedure).
"""

import json
from pathlib import Path

import pytest

from .golden_utils import (
    normalize_meta,
    normalize_metrics_rows,
    verify_golden,
)

pytestmark = pytest.mark.e2e

FIXTURE = Path(__file__).parent / "fixtures" / "input" / "krakow_2024_mini"
GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden"
SOLVERS = ["GREEDY", "MES_UTILS", "MES_ADD1"]
METRICS = [
    "EXCLUSION_RATION",
    "SUM_OBJECTIVES",
    "EJR_PLUS",
    "CONSTRAINTS",
    "INSTANCE_SIZE",
    "TOTAL_COST",
]


def test_e2e_golden(tmp_path):
    import analyzerRunner
    import experimentRunner

    # trailing slashes required: runner/analyzer concat paths as f-strings
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
                "utility_type": "COST_ORDINAL",
                "source_directory_path": str(FIXTURE),
                "constraints_configs": [],
            }
            for solver in SOLVERS
        ],
    }
    experimentRunner.main(experiment)

    meta_paths = sorted(Path(results_path).glob("meta_*.json"))
    assert len(meta_paths) == len(SOLVERS)
    assert len(sorted(Path(results_path).glob("problem_*.lp"))) == len(SOLVERS)
    actual_metas = {}
    for meta_path in meta_paths:
        meta = json.loads(meta_path.read_text())
        actual_metas[meta["solver"]] = normalize_meta(meta)
    assert sorted(actual_metas) == sorted(SOLVERS)

    analyzer = {
        "analyzer_result_path": analysis_path,
        "experiment_results_base_path": results_path,
        "metrics": METRICS,
    }
    analyzerRunner.main(analyzer)

    # metrics-results.json: analyzer names file after results dir basename
    rows = json.loads(
        (Path(analysis_path) / "metrics-results.json").read_text()
    )
    actual_rows = normalize_metrics_rows(rows)

    regenerated = [
        path
        for path in (
            verify_golden(actual_metas, GOLDEN_DIR / "selected.json"),
            verify_golden(actual_rows, GOLDEN_DIR / "metrics.json"),
        )
        if path
    ]
    if regenerated:
        pytest.fail(
            f"golden regenerated: {[p.name for p in regenerated]} — "
            "inspect + commit separately (UPDATE_GOLDEN must not green CI)"
        )
