from helpers.analyzers.metrics import Metric, get_metric_strategy
from helpers.runners.model import RunnerResult
from helpers.utils.utils import read_from_json
from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem


if __name__ == '__main__':
    data: RunnerResult = read_from_json("resources/results/latest.json")
    problem: MultiObjectiveLpProblem = MultiObjectiveLpProblem.from_dict(data['problem'])
    print(problem)
    print(get_metric_strategy(Metric.NON_ZERO_OBJECTIVES)(problem))
    print(get_metric_strategy(Metric.SUM_OBJECTIVES)(problem))
