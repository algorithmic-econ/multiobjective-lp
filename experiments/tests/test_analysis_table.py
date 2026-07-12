import pytest

from helpers.analyzers.analysis_table import (
    transform_metrics_to_markdown_table,
)
from helpers.utils.utils import write_to_json


def test_filename_regex_miss_raises_with_filename(tmp_path):
    metrics_path = tmp_path / "metrics.json"
    write_to_json(
        metrics_path,
        [{"problem_path": "results/meta_bad_file.json", "metrics": []}],
    )
    with pytest.raises(ValueError, match="meta_bad_file.json"):
        transform_metrics_to_markdown_table(metrics_path, limit=None)
