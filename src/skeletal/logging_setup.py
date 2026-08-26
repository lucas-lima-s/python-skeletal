import logging
import sys
from logging.handlers import RotatingFileHandler

from skeletal.config import Settings

_LOGGER_NAME = "skeletal"
_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"
_MANAGED_ATTR = "_skeletal_managed"


def configure_logging(settings: Settings) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)

    for handler in list(logger.handlers):
        if getattr(handler, _MANAGED_ATTR, False):
            logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(fmt=_FORMAT, datefmt=_DATEFMT)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    setattr(stream_handler, _MANAGED_ATTR, True)
    logger.addHandler(stream_handler)

    if settings.log_to_file:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.log_dir / "app.log",
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        setattr(file_handler, _MANAGED_ATTR, True)
        logger.addHandler(file_handler)

    logger.setLevel(settings.log_level)
    logger.propagate = False
    logging.captureWarnings(True)

    return logger
