import json
from typing import Any

import orjson
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """
    Since aiologger doesn't support custom formatting,
    we match all other loggers to its output format
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "logged_at": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "line_number": record.lineno,
            "function": record.funcName,
            "level": record.levelname,
            "file_path": record.pathname,
            "msg": record.getMessage(),
        }
        return json.dumps(log_data)


def orjson_serializer_to_str(obj: Any, **_: object) -> str:
    """Kwargs for compatibility with aiologger"""
    return orjson.dumps(obj).decode()


class OrjsonFormatter(logging.Formatter):
    """
    Since aiologger doesn't support custom formatting,
    we match all other loggers to its output format
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "logged_at": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "line_number": record.lineno,
            "function": record.funcName,
            "level": record.levelname,
            "file_path": record.pathname,
            "msg": record.getMessage(),
        }
        return orjson_serializer_to_str(log_data)
