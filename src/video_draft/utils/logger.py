"""Structured logging utilities supporting JSON-lines and clean text output."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured extra fields if present
        if hasattr(record, "structured_data") and isinstance(record.structured_data, dict):
            log_obj.update(record.structured_data)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Adapter to easily pass structured payloads into logging calls."""

    def process(self, msg: Any, kwargs: Any) -> tuple[Any, Any]:
        standard_keys = {"exc_info", "stack_info", "stacklevel", "extra"}
        extra = dict(kwargs.get("extra") or {})
        structured = {}
        filtered_kwargs = {}

        for k, v in kwargs.items():
            if k in standard_keys:
                filtered_kwargs[k] = v
            else:
                structured[k] = v

        if structured:
            existing = extra.get("structured_data", {})
            if isinstance(existing, dict):
                existing.update(structured)
                extra["structured_data"] = existing
            else:
                extra["structured_data"] = structured

        filtered_kwargs["extra"] = extra
        return msg, filtered_kwargs


def setup_logger(
    name: str = "video_draft",
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str | Path] = None,
) -> StructuredLoggerAdapter:
    """Configures and returns a structured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
        )
    logger.addHandler(console_handler)

    # Optional file handler (always writes JSON for reproducibility)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return StructuredLoggerAdapter(logger, {})
