from helpers.runners.model import RunnerResult
from helpers.utils.utils import read_from_json

if __name__ == '__main__':
    data: RunnerResult = read_from_json("resources/results/latest.json")
    print(data['problem'])
