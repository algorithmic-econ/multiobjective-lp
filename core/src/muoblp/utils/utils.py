from typing import TypeVar

T = TypeVar("T")


def flatten(collection: list[list[T]]) -> list[T]:
    return [x for xs in collection for x in xs]


def get_geometric_ratios(numbers: list[float]) -> list[float]:
    ratios = []
    for i in range(len(numbers) - 1):
        ratios.append(numbers[i + 1] / numbers[i])
    return ratios
