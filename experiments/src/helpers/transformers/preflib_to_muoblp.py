from muoblp.model.multi_objective_lp import MultiObjectiveLpProblem
from pathlib import Path
from pulp import LpVariable, LpBinary, lpSum
import re


def parse_line(line: str):
    left, right = line.split(":", 1)
    count = int(left.strip())

    ranking = []
    token = ""
    inside = False

    for ch in right:
        if ch == "{":
            if inside:
                raise RuntimeError("Cannot parse:", line)
            token = ""
            inside = True
        elif ch == "}":
            if not inside:
                raise RuntimeError("Cannot parse:", line)
            ranking.append(
                [int(x.strip()) for x in token.split(",") if x.strip()]
            )
            token = ""
            inside = False
        elif ch == "," and not inside:
            if token.strip():
                ranking.append([int(token.strip())])
                token = ""
            else:
                raise RuntimeError("Cannot parse:", line)
        else:
            token += ch

    if last := token.strip():
        ranking.append([int(last)])

    return count, ranking


def load_preflib(filename: Path):
    candidate_names = {}
    title = str(filename)
    m = 0
    votes = []
    with open(filename) as f:
        re_title = re.compile(r"# TITLE: (.*)\n")
        re_number_alternatives = re.compile(r"# NUMBER ALTERNATIVES: (\d+)\n")
        re_candidate_name = re.compile(r"# ALTERNATIVE NAME (\d+): (.*)\n")
        for line in f:
            if line.startswith("#"):
                res = re_title.fullmatch(line)
                if res:
                    title = res.group(1)
                    continue
                res = re_number_alternatives.fullmatch(line)
                if res:
                    m = int(res.group(1))
                    continue
                res = re_candidate_name.fullmatch(line)
                if res:
                    candidate_names[int(res.group(1))] = res.group(2)
                    continue
                print(line, end="")
            else:
                try:
                    votes.append(parse_line(line))
                except RuntimeError as e:
                    raise RuntimeError(f"Error parsing file {filename}") from e

    if m == 0:
        raise RuntimeError(
            f"Error parsing file {filename}: undefined number of alternatives"
        )

    variables = {
        num: LpVariable(name, 0, 1, LpBinary)
        for num, name in candidate_names.items()
    }

    objectives = []
    for i, (_, ranking) in enumerate(votes):
        curr = m
        u = {}
        for group in ranking:
            for c in group:
                u[c] = curr
            curr -= len(group)
        objective = lpSum([utility * variables[c] for c, utility in u.items()])
        objective.name = f"v{i + 1}"
        objectives.append(objective)

    weights = {f"v{i + 1}": weight for i, (weight, _) in enumerate(votes)}

    problem = MultiObjectiveLpProblem(title)
    problem.addVariables(variables.values())
    problem.set_objectives(objectives)
    problem.set_objectives_weights(weights)

    return problem
