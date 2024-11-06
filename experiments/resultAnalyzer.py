from datetime import datetime

from helpers.analyzers.metrics import Metric, get_metrics
from helpers.runners.model import RunnerResult
from helpers.utils.utils import read_from_json, write_to_json
from multiobjective_lp.model.multi_objective_lp import MultiObjectiveLpProblem

if __name__ == '__main__':
    data: RunnerResult = read_from_json("resources/solver-results/latest.json")
    problem: MultiObjectiveLpProblem = MultiObjectiveLpProblem.from_dict(data['problem'])

    result = get_metrics([Metric.NON_ZERO_OBJECTIVES, Metric.SUM_OBJECTIVES], problem)

    basePath = 'resources/analyzer-results/'
    write_to_json(
        # f"{basePath}{datetime.now().isoformat(timespec='seconds')}_{data['source']}_{data['solver']}.json",
        f"{basePath}latest.json",
        result)
    print(result)
