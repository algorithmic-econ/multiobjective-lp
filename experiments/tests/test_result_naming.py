import time
import uuid

from helpers.utils.result_naming import (
    data_source_name,
    new_run_id,
    run_dir_name,
)


def test_data_source_name_strips_pb_extension():
    assert data_source_name("input/krakow_2024/x.pb") == "x"


def test_data_source_name_directory_source():
    assert data_source_name("input/krakow_2024") == "krakow_2024"


def test_new_run_id_is_uuid7():
    assert uuid.UUID(new_run_id()).version == 7


def test_new_run_ids_sort_by_creation_time():
    first = new_run_id()
    time.sleep(0.002)
    assert first < new_run_id()


def test_run_dir_name_builds_exact_shape():
    name = run_dir_name("RUNID", "krakow", "COST", "GREEDY", "abc123")
    assert name == "RUNID_krakow_COST_GREEDY_abc123"
