import logging
from pathlib import Path

from skeletal.config import Settings
from skeletal.logging_setup import configure_logging


def _managed_handlers(logger: logging.Logger) -> list[logging.Handler]:
    return [h for h in logger.handlers if getattr(h, "_skeletal_managed", False)]


def test_idempotent_no_handler_duplication(tmp_cwd: Path) -> None:
    settings = Settings()
    logger = configure_logging(settings)
    configure_logging(settings)
    assert len(_managed_handlers(logger)) == 2


def test_stream_only_when_log_to_file_false(tmp_cwd: Path) -> None:
    settings = Settings(log_to_file=False)
    logger = configure_logging(settings)
    handlers = _managed_handlers(logger)
    assert len(handlers) == 1
    assert isinstance(handlers[0], logging.StreamHandler)


def test_file_created_and_written_when_log_to_file_true(tmp_cwd: Path) -> None:
    settings = Settings(log_to_file=True, log_dir=tmp_cwd / "logs")
    logger = configure_logging(settings)
    logger.info("hello from test")
    log_file = settings.log_dir / "app.log"
    assert log_file.is_file()
    assert "hello from test" in log_file.read_text(encoding="utf-8")


def test_level_propagates(tmp_cwd: Path) -> None:
    settings = Settings(log_to_file=False, log_level="DEBUG")
    logger = configure_logging(settings)
    assert logger.level == logging.DEBUG
    assert logger.propagate is False
