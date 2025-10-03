"""Structured logging configuration for StoryMachine."""

import inspect
import os
from pathlib import Path

import structlog


def configure_logging() -> None:
    """Configure structured logging with JSON output to file."""
    log_file = Path("storymachine.log")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
        logger_factory=structlog.WriteLoggerFactory(file=log_file.open("a")),
        cache_logger_on_first_use=False,
    )


def get_logger() -> structlog.BoundLogger:
    """Get a logger with automatic file and function context."""
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_frame = frame.f_back
        func_name = caller_frame.f_code.co_name
        file_name = os.path.basename(caller_frame.f_code.co_filename)

        return structlog.get_logger().bind(
            file=file_name,
            function=func_name,
        )

    return structlog.get_logger()


# Configure logging on import
configure_logging()
