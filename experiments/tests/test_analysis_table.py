from helpers.analyzers.analysis_table import (
    transform_metrics_to_markdown_table,
)
from helpers.utils.utils import write_to_json


def test_table_built_from_row_fields_not_filename(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    write_to_json(
        metrics_path,
        [
            {
                "problem_path": "results/meta_bad_file.json",
                "city": "krakow_2024_mini",
                "utility": "COST",
                "solver": "GREEDY",
                "metrics": ["SUM_OBJECTIVES"],
                "SUM_OBJECTIVES": {"sum": 100},
            }
        ],
    )
    table = transform_metrics_to_markdown_table(metrics_path, limit=None)
    assert "krakow 2024 mini" in table
    assert "COST" in table
    assert "GREEDY" in table
    assert "100" in table


def test_failure_row_skipped_other_rows_still_render(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    write_to_json(
        metrics_path,
        [
            {
                "meta_path": "results/meta_broken.json",
                "error_type": "ValidationError",
                "error_message": "boom",
            },
            {
                "problem_path": "results/meta_ok.json",
                "city": "krakow_2024",
                "utility": "COST",
                "solver": "GREEDY",
                "metrics": ["SUM_OBJECTIVES"],
                "SUM_OBJECTIVES": {"sum": 42},
            },
        ],
    )
    table = transform_metrics_to_markdown_table(metrics_path, limit=None)
    assert "krakow 2024" in table
    assert "42" in table


def test_all_failure_rows_returns_no_analyzable_rows_message(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    write_to_json(
        metrics_path,
        [
            {
                "meta_path": "results/meta_broken.json",
                "error_type": "ValidationError",
                "error_message": "boom",
            }
        ],
    )
    assert (
        transform_metrics_to_markdown_table(metrics_path, limit=None)
        == "no analyzable rows"
    )


def test_empty_input_returns_no_analyzable_rows_message(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    write_to_json(metrics_path, [])
    assert (
        transform_metrics_to_markdown_table(metrics_path, limit=None)
        == "no analyzable rows"
    )
