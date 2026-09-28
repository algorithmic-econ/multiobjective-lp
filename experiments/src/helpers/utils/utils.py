import json
from pathlib import Path
from typing import Any

import json5


def write_to_json(path: Path, data: Any) -> None:
    processor = json5 if path.suffix == ".jsonc" else json
    with open(path, "w", encoding="utf-8") as file:
        processor.dump(data, file, ensure_ascii=False, indent=4)


def read_from_json(path: Path) -> Any:
    processor = json5 if path.suffix == ".jsonc" else json
    with open(path, "r", encoding="utf-8") as file:
        return processor.load(file)
