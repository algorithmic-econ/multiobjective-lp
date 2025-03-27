from pulp import LpAffineExpression


def expression_to_lp_format(
    expression: LpAffineExpression, constant: int = 1
) -> str:
    """
    copy-paste of `LpAffineExpression::asCplexLpAffineExpression` with line length limit modification
    returns a string that represents the Affine Expression in lp format
    """
    # refactored to use a list for speed in iron python
    result, line = expression_to_variables_only(expression)
    if not expression:
        term = f" {expression.constant}"
    else:
        term = ""
        if constant:
            if expression.constant < 0:
                term = " - %s" % (-expression.constant)
            elif expression.constant > 0:
                term = f" + {expression.constant}"
    line += [term]
    result += ["".join(line)]
    result = "%s\n" % "\n".join(result)
    return result


def expression_to_variables_only(expression: LpAffineExpression):
    """
    helper for expression_to_lp_format
    copy-paste of `LpAffineExpression::asCplexVariablesOnly` with line length limit modification
    """
    result = []
    line = [f"{expression.name}:"]
    notFirst = 0
    variables = expression.sorted_keys()
    for v in variables:
        val = expression[v]
        if val < 0:
            sign = " -"
            val = -val
        elif notFirst:
            sign = " +"
        else:
            sign = ""
        notFirst = 1
        if val == 1:
            term = f"{sign} {v.name}"
        else:
            # adding zero to val to remove instances of negative zero
            term = f"{sign} {val + 0:.12g} {v.name}"

        line += [term]
    return result, line
