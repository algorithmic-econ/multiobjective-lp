import logging
import logging.config
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "logging_config.yaml"
)


def setup_logging(config_path=DEFAULT_CONFIG_PATH):
    try:
        with open(config_path, "rt") as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.error(
            f"Error loading logging configuration: {e}", exc_info=True
        )
