"""Logging configuration for Medtech RAG solution."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory

from .config import get_config


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    use_json: bool = True
) -> None:
    """Configure structured logging for the application."""
    config = get_config()
    
    # Use provided log level or get from config
    log_level = log_level or config.settings.log_level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure standard library logging
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        stream=sys.stdout,
    )
    
    # Set up log file if specified in config
    if log_file is None and config.yaml_config.get("logging", {}).get("file", {}).get("enabled"):
        log_path = Path(config.yaml_config["logging"]["file"]["path"])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_file = log_path
    
    # Add file handler if log file is specified
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=config.yaml_config.get("logging", {}).get("file", {}).get("max_size_mb", 10) * 1024 * 1024,
            backupCount=config.yaml_config.get("logging", {}).get("file", {}).get("backup_count", 5)
        )
        file_handler.setLevel(numeric_level)
        logging.getLogger().addHandler(file_handler)
    
    # Configure processors based on format preference
    if use_json and config.yaml_config.get("logging", {}).get("format") == "json":
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_app_context,
            structlog.processors.JSONRenderer()
        ]
    else:
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_app_context,
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def add_app_context(logger, log_method, event_dict):
    """Add application context to all log entries."""
    config = get_config()
    event_dict["environment"] = config.settings.environment
    event_dict["app_name"] = config.yaml_config.get("app", {}).get("name", "medtech-rag")
    event_dict["app_version"] = config.yaml_config.get("app", {}).get("version", "unknown")
    return event_dict


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Convenience function to set up logging with defaults
def init_logging():
    """Initialize logging with default settings."""
    setup_logging()


# Example usage in other modules:
# from common.logging_config import get_logger
# logger = get_logger(__name__)
# logger.info("Processing document", document_id=doc_id, size=file_size)