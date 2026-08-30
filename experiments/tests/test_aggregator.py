import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from helpers.analyzers.model import AggregatorConfig, AnalyzerResult

GOLDEN_METRICS = Path(__file__).parent / "fixtures" / "golden" / "metrics.json"


def _rows_with_time(tmp_path: Path) -> Path:
    """Golden metrics.json has `time` stripped (D11 normalization) - not a
    valid AnalyzerResult on its own. Reinject a fixed value for tests that
    need to load it as real rows."""
    entries = json.loads(GOLDEN_METRICS.read_text())
    for entry in entries:
        entry["time"] = 1.0
    path = tmp_path / "metrics_with_time.json"
    path.write_text(json.dumps(entries))
    return path


def _base_config(**overrides):
    defaults = {
        "metrics_json_path": str(GOLDEN_METRICS),
        "output_path": "out.png",
        "group_by": "instance_size_bucket",
    }
    defaults.update(overrides)
    return AggregatorConfig.model_validate(defaults)


def test_minimal_config_validates():
    config = _base_config()
    assert config.bucket_size == 10
    assert config.exclude_cities == []
    assert config.include_solvers is None
    assert config.normalize_baseline is None
    assert config.clip_upper == 5.0


def test_unknown_key_rejected():
    with pytest.raises(ValidationError) as exc_info:
        AggregatorConfig.model_validate(
            {
                "metrics_json_path": "x",
                "output_path": "y",
                "group_by": "city",
                "bogus": 1,
            }
        )
    assert any(e["loc"] == ("bogus",) for e in exc_info.value.errors())


def test_bad_group_by_rejected():
    with pytest.raises(ValidationError):
        _base_config(group_by="not_a_mode")


def test_load_rows_golden_all_valid(tmp_path):
    from aggregate_results import load_rows

    rows = load_rows(_rows_with_time(tmp_path))
    assert len(rows) == 3
    assert all(isinstance(row, AnalyzerResult) for row in rows)
    assert {row.solver for row in rows} == {"GREEDY", "MES_ADD1", "MES_UTILS"}


def test_load_rows_skips_invalid(tmp_path):
    from aggregate_results import load_rows

    valid_row = json.loads(_rows_with_time(tmp_path).read_text())[0]
    bad_path = tmp_path / "bad.json"
    bad_path.write_text(json.dumps([None, valid_row, {"not": "valid"}]))

    rows = load_rows(bad_path)
    assert len(rows) == 1
    assert rows[0].solver == "GREEDY"


def test_build_dataframe_bucket_mode_row_count_and_bucket_value(tmp_path):
    from aggregate_results import build_dataframe, load_rows

    rows = load_rows(_rows_with_time(tmp_path))
    config = _base_config(bucket_size=10)
    df = build_dataframe(rows, config)

    # 4 metrics (EXCLUSION_RATION, SUM_OBJECTIVES, TOTAL_COST, EJR_PLUS) + 1 time row, per solver
    assert len(df) == 3 * 5
    assert set(df["Bucket"].unique()) == {10}


def test_build_dataframe_normalization_and_clip(tmp_path):
    from aggregate_results import build_dataframe, load_rows

    rows = load_rows(_rows_with_time(tmp_path))
    config = _base_config(normalize_baseline="GREEDY", clip_upper=1.05)
    df = build_dataframe(rows, config)

    sum_rows = df[df["Metric"] == "Sum Objectives (rel. to Greedy)"]
    greedy_val = sum_rows[sum_rows["Solver"] == "GREEDY"]["Value"].iloc[0]
    assert greedy_val == pytest.approx(1.0)
    assert (sum_rows["Value"] <= 1.05).all()


def test_build_dataframe_filters(tmp_path):
    from aggregate_results import build_dataframe, load_rows

    rows = load_rows(_rows_with_time(tmp_path))

    excluded = build_dataframe(
        rows, _base_config(exclude_cities=["krakow_2024_mini"])
    )
    assert excluded.empty

    included = build_dataframe(rows, _base_config(include_solvers=["GREEDY"]))
    assert set(included["Solver"].unique()) == {"GREEDY"}


def test_build_dataframe_city_mode_mean_over_years(tmp_path):
    from aggregate_results import build_dataframe

    rows_raw = json.loads(_rows_with_time(tmp_path).read_text())[:1]
    row_2023 = dict(rows_raw[0])
    row_2023["city"] = "krakow_2023"
    row_2023["SUM_OBJECTIVES"] = {"sum": 100.0}
    row_2024 = dict(rows_raw[0])
    row_2024["city"] = "krakow_2024"
    row_2024["SUM_OBJECTIVES"] = {"sum": 200.0}

    rows = [
        AnalyzerResult.model_validate(row_2023),
        AnalyzerResult.model_validate(row_2024),
    ]
    df = build_dataframe(rows, _base_config(group_by="city"))

    assert "Bucket" not in df.columns
    sum_rows = df[df["Metric"] == "Sum Objectives"]
    assert sum_rows["City"].tolist() == ["Krakow"]
    assert sum_rows["Value"].iloc[0] == pytest.approx(150.0)


@pytest.mark.parametrize("group_by", ["instance_size_bucket", "city"])
def test_plot_smoke(tmp_path, monkeypatch, group_by):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    from aggregate_results import build_dataframe, load_rows, plot

    rows = load_rows(_rows_with_time(tmp_path))
    output_path = tmp_path / "out.png"
    config = _base_config(
        group_by=group_by,
        output_path=str(output_path),
        normalize_baseline="GREEDY"
        if group_by == "instance_size_bucket"
        else None,
    )
    df = build_dataframe(rows, config)
    plot(df, config)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_main_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("MPLBACKEND", "Agg")
    from aggregate_results import main

    metrics_path = _rows_with_time(tmp_path)
    output_path = tmp_path / "out.png"
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "metrics_json_path": str(metrics_path),
                "output_path": str(output_path),
                "group_by": "city",
            }
        )
    )

    result = main(config_path)
    assert result == output_path
    assert output_path.exists()
