import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import Settings, get_settings


LOGGER_NAME = "agentic_rag_system"


def configure_logging(settings: Settings | None = None) -> logging.Logger:
    """Configure application logging once and return the project logger."""
    settings = settings or get_settings()
    log_directory = Path(settings.log_directory)
    log_directory.mkdir(parents=True, exist_ok=True)
    app_log_path = log_directory / settings.log_file
    error_log_path = log_directory / settings.error_log_file

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    app_handler_exists = _find_file_handler(logger, app_log_path, "agentic_rag_file_handler") is not None
    error_handler_exists = (
        _find_file_handler(logger, error_log_path, "agentic_rag_error_file_handler") is not None
    )
    if not app_handler_exists or not error_handler_exists:
        _remove_managed_handlers(logger)
        logger.addHandler(
            _build_file_handler(
                log_path=app_log_path,
                name="agentic_rag_file_handler",
                level=logging.INFO,
                max_bytes=settings.log_max_bytes,
                backup_count=settings.log_backup_count,
            )
        )
        logger.addHandler(
            _build_file_handler(
                log_path=error_log_path,
                name="agentic_rag_error_file_handler",
                level=logging.WARNING,
                max_bytes=settings.log_max_bytes,
                backup_count=settings.log_backup_count,
            )
        )

    return logger


def get_logger() -> logging.Logger:
    """Return the configured project logger."""
    return configure_logging()


def _build_file_handler(
    log_path: Path,
    name: str,
    level: int,
    max_bytes: int,
    backup_count: int,
) -> RotatingFileHandler:
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.set_name(name)
    file_handler.setLevel(level)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    )
    return file_handler


def _find_file_handler(logger: logging.Logger, log_path: Path, name: str) -> logging.Handler | None:
    expected_path = str(log_path.resolve())
    for handler in logger.handlers:
        if not isinstance(handler, RotatingFileHandler):
            continue
        if handler.get_name() != name:
            continue
        if Path(handler.baseFilename).resolve() == Path(expected_path):
            return handler
    return None


def _remove_managed_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        if handler.get_name() not in {"agentic_rag_file_handler", "agentic_rag_error_file_handler"}:
            continue
        logger.removeHandler(handler)
        handler.close()
