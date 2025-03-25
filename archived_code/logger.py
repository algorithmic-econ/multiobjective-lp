import logging
import datetime
import os
import io
from enum import Enum


def get_current_filename() -> str:
    return f"log_{datetime.datetime.now().isoformat(timespec='seconds')}.log"


report_stream = io.StringIO()
memory_handler = logging.StreamHandler(stream=report_stream)
memory_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
)

file_handler = logging.FileHandler("output/" + get_current_filename())
file_handler.setFormatter(
    logging.Formatter("%(asctime)s|%(levelname)s|%(message)s", datefmt="%H:%M:%S")
)

logger = logging.getLogger("multiobjective-lp")
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
logger.addHandler(memory_handler)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_logs_from_stream() -> str:
    return report_stream.getvalue()


class LogKey(Enum):
    PROJECT = "PROJECT"
    FEAS_RATIO = "FEAS_RATIO"
