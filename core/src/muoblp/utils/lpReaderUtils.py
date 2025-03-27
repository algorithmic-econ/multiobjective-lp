from pulp import (
    LpMaximize,
    LpMinimize,
    LpVariable,
    LpBinary,
    LpConstraintLE,
    LpConstraintGE,
    LpConstraint,
    LpAffineExpression,
)

from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem


def get_constraint_sign(constraint: str) -> int:
    if "<=" in constraint:
        return constraint.index("<")
    if ">=" in constraint:
        return constraint.index(">")
    raise Exception("Unexpected constraint sign")


def read_lp_file(filename) -> MultiObjectiveLpProblem:
    problem_data = {
        "name": "",
        "sense": None,  # 'Minimize' or 'Maximize'
        "constraints": [],
        "variables": {},
        "objectives": [],
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
            for coef, var in [coef_var.strip().split(" ")]
        ]

        c_sense = (
            LpConstraintLE
            if constraint_line[sign_idx : sign_idx + 2] == "<="
            else LpConstraintGE
        )
        c_rhs = int(constraint_line[sign_idx + 2 :].strip())
        constraint = LpConstraint.from_dict(
            {
                "coefficients": LpAffineExpression(c_lhs),
                "constant": -c_rhs,
                "name": c_name,
                "sense": c_sense,
                "pi": -0.0,  # TODO: What should be the value?
            }
        )
        problem_data["constraints"].append(constraint)

    for target_line in lines[
        lines.index("OBJECTIVES:\n") + 1 : lines.index("END_OBJECTIVES:\n")
    ]:
        name_right_idx = target_line.index(":")
        t_name = target_line[:name_right_idx]
        target = LpAffineExpression(
            [
                [problem_data["variables"][var.strip()], 1]
                for var in target_line[name_right_idx + 2 :].split("+")
            ],
            name=t_name,
        )
        problem_data["objectives"].append(target)

    problem = MultiObjectiveLpProblem(
        problem_data["name"], problem_data["sense"], problem_data["objectives"]
    )
    problem.addVariables(problem_data["variables"].values())
    for constraint in problem_data["constraints"]:
        problem.addConstraint(constraint)

    return problem
