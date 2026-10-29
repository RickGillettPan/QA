import logging
from pathlib import Path


LOG_PATH = Path(__file__).with_name("automation.log")
LOGGER_NAME = "tvmaze"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not any(
        isinstance(handler, logging.FileHandler)
        and Path(handler.baseFilename) == LOG_PATH.resolve()
        for handler in logger.handlers
    ):
        handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
