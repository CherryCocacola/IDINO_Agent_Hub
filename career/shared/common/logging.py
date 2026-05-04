"""
Centralized logging configuration for all microservices.
Supports both console and file-based logging with rotation.
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import json

# Default log directory - can be overridden by LOG_DIR environment variable
DEFAULT_LOG_DIR = Path(__file__).parent.parent.parent / "logs"


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


class ServiceLogger(logging.Logger):
    """Custom logger with additional context methods."""

    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)

    def with_context(self, **kwargs) -> "ServiceLogger":
        """Add context to log messages."""

        class ContextAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs_inner):
                extra = kwargs_inner.setdefault("extra", {})
                extra["extra_fields"] = self.extra
                return msg, kwargs_inner

        return ContextAdapter(self, kwargs)


def setup_logging(
    service_name: str,
    log_level: Optional[str] = None,
    json_format: bool = True,
    log_to_file: bool = True,
    log_dir: Optional[Path] = None
) -> None:
    """
    Configure logging for a microservice.

    Args:
        service_name: Name of the service for log identification
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting
        log_to_file: Whether to also log to files
        log_dir: Directory for log files (defaults to project logs/)
    """
    level = log_level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Set custom logger class
    logging.setLoggerClass(ServiceLogger)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    if json_format:
        file_formatter = JSONFormatter(service_name)
        console_formatter = JSONFormatter(service_name)
    else:
        fmt = f"%(asctime)s | {service_name} | %(levelname)s | %(name)s | %(message)s"
        file_formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
        console_formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Create file handlers if enabled
    if log_to_file:
        log_directory = log_dir or Path(os.getenv("LOG_DIR", DEFAULT_LOG_DIR))
        log_directory.mkdir(parents=True, exist_ok=True)

        # Main log file with rotation (10MB, keep 5 backups)
        main_log_file = log_directory / f"{service_name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        # Error-only log file
        error_log_file = log_directory / f"{service_name}.error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)

        # Combined log for all services
        combined_log_file = log_directory / "combined.log"
        combined_handler = logging.handlers.RotatingFileHandler(
            combined_log_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=3,
            encoding="utf-8"
        )
        combined_handler.setLevel(numeric_level)
        combined_handler.setFormatter(file_formatter)
        root_logger.addHandler(combined_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)


def get_logger(name: str) -> ServiceLogger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)
