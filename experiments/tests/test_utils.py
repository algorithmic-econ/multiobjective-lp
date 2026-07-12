import pytest

from helpers.utils.utils import read_from_json, write_to_json

DATA = {"name": "sample", "values": [1, 2, 3], "nested": {"ok": True}}


@pytest.mark.parametrize("suffix", [".json", ".jsonc"])
def test_write_read_roundtrip(tmp_path, suffix):
    path = tmp_path / f"data{suffix}"
    write_to_json(path, DATA)
    assert read_from_json(path) == DATA


def test_read_jsonc_with_comments(tmp_path):
    path = tmp_path / "config.jsonc"
    path.write_text('{\n  // comment\n  "a": 1,\n}\n', encoding="utf-8")
    assert read_from_json(path) == {"a": 1}
