import re

from helpers.utils.result_naming import (
    PROBLEM_ID_PATTERN,
    data_source_name,
    new_problem_id,
    result_filename,
    result_filename_pattern,
)


def test_data_source_name_strips_pb_extension():
    assert data_source_name("input/krakow_2024/x.pb") == "x"


def test_data_source_name_directory_source():
    assert data_source_name("input/krakow_2024") == "krakow_2024"


def test_new_problem_id_matches_pattern():
    assert re.fullmatch(PROBLEM_ID_PATTERN, new_problem_id())


def test_result_filename_builds_exact_shape():
    name = result_filename(
        "meta", "json", "07-20T10-00-00_ab12", "krakow", "COST", "GREEDY"
    )
    assert name == "meta_07-20T10-00-00_ab12_krakow_COST_GREEDY.json"


def test_result_filename_pattern_matches_built_name():
    pattern = result_filename_pattern(
        "meta", "json", "krakow", "COST", "GREEDY"
    )
    built = result_filename(
        "meta", "json", new_problem_id(), "krakow", "COST", "GREEDY"
    )
    assert pattern.match(built)


def test_result_filename_pattern_rejects_mismatch():
    pattern = result_filename_pattern(
        "meta", "json", "krakow", "COST", "GREEDY"
    )
    other_solver = result_filename(
        "meta", "json", new_problem_id(), "krakow", "COST", "MES_ADD1"
    )
    assert pattern.match(other_solver) is None
