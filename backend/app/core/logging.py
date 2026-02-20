import json
import logging
import sys
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
clinic_id_var: ContextVar[str] = ContextVar("clinic_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(""),
            "clinic_id": clinic_id_var.get(""),
            "user_id": user_id_var.get(""),
        }
        if record.exc_info and record.exc_info[1]:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


class DevFormatter(logging.Formatter):
    """Human-readable log formatter for development."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_var.get("")
        prefix = f"[{req_id[:8]}] " if req_id else ""
        record.msg = f"{prefix}{record.msg}"
        return super().format(record)


def setup_logging(app_env: str = "development", app_debug: bool = False) -> None:
    level = logging.DEBUG if app_debug else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if app_env == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            DevFormatter(fmt="%(asctime)s %(levelname)-8s %(name)s - %(message)s")
        )

    root_logger.addHandler(handler)

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.WARNING if not app_debug else logging.INFO
    )
