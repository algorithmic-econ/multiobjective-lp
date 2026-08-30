import pytest
from pulp import LpAffineExpression, LpVariable

from muoblp.utils.lp_writer_utils import expression_to_lp_format


def test_integral_float_coefficient_is_written_as_integer():
    variable = LpVariable("p1", cat="Binary")
    expression = LpAffineExpression({variable: 2.0}, name="o")

    assert expression_to_lp_format(expression) == "o: 2 p1\n"


def test_unit_coefficient_is_written_without_a_coefficient():
    variable = LpVariable("p1", cat="Binary")
    expression = LpAffineExpression({variable: 1}, name="o")

    assert expression_to_lp_format(expression) == "o: p1\n"


def test_non_integer_coefficient_raises_naming_the_variable():
    variable = LpVariable("p1", cat="Binary")
    expression = LpAffineExpression({variable: 2.5}, name="o")

    with pytest.raises(ValueError) as error:
        expression_to_lp_format(expression)

    assert "p1" in str(error.value)
    assert "2.5" in str(error.value)
