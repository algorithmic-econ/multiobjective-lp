import json
from pathlib import Path

import json5


def write_to_json(path: Path, data):
    processor = json5 if path.suffix == "jsonc" else json
    with open(path, "w", encoding="utf-8") as file:
        processor.dump(data, file, ensure_ascii=False, indent=4)


def read_from_json(path: Path):
    processor = json5 if path.suffix == "jsonc" else json
    with open(path, "r", encoding="utf-8") as file:
        return processor.load(file)
