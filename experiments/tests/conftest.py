import pytest

# golden_utils asserts golden equality; without rewrite failures show no diff
pytest.register_assert_rewrite("tests.golden_utils")

from .fixtures.pabutools_factories import (
    single_district_setup,
    multi_district_setup,
)
