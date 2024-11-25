from helpers.utils.enhanceFromSolverResult import enhance_from_solver_result
from helpers.analyzers.metrics import Metric, get_metrics
from helpers.runners.model import RunnerResult
from helpers.utils.utils import read_from_json, write_to_json
from multiobjective_lp.utils.lpReaderUtils import read_lp_file

if __name__ == '__main__':
    solver_result: RunnerResult = read_from_json("resources/solver-results/latest.json")
    problem = read_lp_file(solver_result['problem_path'])
    problem = enhance_from_solver_result(solver_result, problem)

    result = get_metrics([Metric.NON_ZERO_OBJECTIVES, Metric.SUM_OBJECTIVES], problem)

    basePath = 'resources/analyzer-results/'
    write_to_json(
        # f"{basePath}{datetime.now().isoformat(timespec='seconds')}_{data['source']}_{data['solver']}.json",
        f"{basePath}latest.json",
        result)
    print(result)
