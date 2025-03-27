from typing import TypeVar, List

T = TypeVar("T")


def flatten(collection: List[List[T]]) -> List[T]:
    return [x for xs in collection for x in xs]


def get_geometric_ratios(numbers: List[float]) -> List[float]:
    ratios = []
    for i in range(len(numbers) - 1):
        ratios.append(numbers[i + 1] / numbers[i])
    return ratios
