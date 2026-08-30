"""Reader for the LP dialect written by
`MultiObjectiveLpProblem.write_lp` (pulp's `writeLP` output plus the
OBJECTIVES/WEIGHTS sections).

It is a deliberately narrow, hand-rolled parser, not a general LP reader -
see `read_lp_file` for the known limitations.
"""

from pulp import (
    LpAffineExpression,
    LpBinary,
    LpConstraint,
    LpConstraintGE,
    LpConstraintLE,
    LpMaximize,
    LpMinimize,
    LpVariable,
)

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem


def get_constraint_sign(constraint: str) -> int:
    if "<=" in constraint:
        return constraint.index("<")
    if ">=" in constraint:
        return constraint.index(">")
    raise Exception("Unexpected constraint sign")


def read_lp_file(filename) -> MultiObjectiveLpProblem:
    """Read a file written by `MultiObjectiveLpProblem.write_lp`.

    Known limitations (documented, not fixed - this reader only has to
    handle what `write_lp` emits for binary PB programs):

    - Coefficients and right-hand sides are coerced with `int()`; a
      fractional value is truncated. `write_lp` now raises on non-integer
      objective coefficients, so files it produces never hit this.
    - Constraint left-hand sides and objectives are split on `"+"` only,
      so a term written with a `"-"` sign (a negative coefficient) is not
      parsed back correctly.
    - The section markers `Binaries`, `Subject To`, `Bounds`,
      `OBJECTIVES:`, `END_OBJECTIVES:`, `WEIGHTS:`, `END_WEIGHTS:` must be
      present on their own lines, in pulp's `writeLP` order; a missing
      marker raises `ValueError` from `list.index`.
    - Every variable is rebuilt as binary with an initial value of 0;
      declared bounds, variable categories and expression constants in the
      file are ignored.
    """
    problem_data = {
        "name": "",
        "sense": None,  # 'Minimize' or 'Maximize'
        "constraints": [],
        "variables": {},
        "objectives": [],
        "objectives_weights": {},
    }

    with open(filename, "r") as f:
        lines = f.readlines()

    problem_data["name"] = lines[0].split("*")[1].strip()
    problem_data["sense"] = (
        LpMaximize if lines[1].lower().startswith("maximize") else LpMinimize
    )

    for variable_line in lines[
        lines.index("Binaries\n") + 1 : lines.index("End\n")
    ]:
        variable = LpVariable(variable_line.strip(), cat=LpBinary)
        variable.setInitialValue(0)
        problem_data["variables"][variable_line.strip()] = variable

    for constraint_line in lines[
        lines.index("Subject To\n") + 1 : lines.index("Bounds\n")
    ]:
        name_right_idx = constraint_line.index(":")
        sign_idx = get_constraint_sign(constraint_line)
        c_name = constraint_line[:name_right_idx]
        c_lhs_str = constraint_line[name_right_idx + 2 : sign_idx]

        c_lhs = [
            (problem_data["variables"][var], int(coef))
            for coef_var in c_lhs_str.split("+")
            for coef, var in [parse_str_variable_with_coefficient(coef_var)]
        ]

        c_sense = (
            LpConstraintLE
            if constraint_line[sign_idx : sign_idx + 2] == "<="
            else LpConstraintGE
        )
        c_rhs = int(constraint_line[sign_idx + 2 :].strip())
        constraint = LpConstraint(
            LpAffineExpression(c_lhs),
            sense=c_sense,
            name=c_name,
            rhs=c_rhs,
        )
        problem_data["constraints"].append(constraint)

    for target_line in lines[
        lines.index("OBJECTIVES:\n") + 1 : lines.index("END_OBJECTIVES:\n")
    ]:
        name_right_idx = target_line.index(":")
        t_name = target_line[:name_right_idx]
        target = LpAffineExpression(
            [
                parse_variable_with_coefficient(problem_data["variables"], var)
                for var in target_line[name_right_idx + 2 :].split("+")
            ],
            name=t_name,
        )
        problem_data["objectives"].append(target)

    for target_line in lines[
        lines.index("WEIGHTS:\n") + 1 : lines.index("END_WEIGHTS:\n")
    ]:
        name_right_idx = target_line.index(":")
        t_name = target_line[:name_right_idx]
        weight = float(target_line[name_right_idx + 2 :].strip())
        problem_data["objectives_weights"][t_name] = weight

    problem = MultiObjectiveLpProblem(
        problem_data["name"],
        problem_data["sense"],
        problem_data["objectives"],
        problem_data["objectives_weights"],
    )
    problem.addVariables(problem_data["variables"].values())
    for constraint in problem_data["constraints"]:
        problem.addConstraint(constraint)

    return problem


def parse_variable_with_coefficient(
    variables: dict[str, LpVariable], var: str
) -> tuple[LpVariable, int]:
    parts = var.strip().split(" ")
    if len(parts) == 1:
        return (variables[parts[0]], 1)
    if len(parts) == 2:
        return (variables[parts[1]], int(parts[0]))
    raise Exception("Unexpected variable parts")


def parse_str_variable_with_coefficient(variable: str) -> tuple[int, str]:
    parts = variable.strip().split(" ")
    if len(parts) == 1:
        return 1, parts[0]
    if len(parts) == 2:
        return int(parts[0]), parts[1]
    raise Exception("Unexpected variable parts")
