import logging
import logging.config
import yaml


# Improve config file discoverability, depending on invokation path deafult might not work
def setup_logging(config_path="config/logging_config.yaml"):
    try:
        with open(config_path, "rt") as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.error(
            f"Error loading logging configuration: {e}", exc_info=True
        )
